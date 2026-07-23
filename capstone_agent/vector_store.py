"""Semantic vector store — Vertex AI embeddings over the clinical corpus.

Google tooling, chosen deliberately for this corpus size and deployment shape:

- **Vertex AI ``gemini-embedding-001``** (via Application Default Credentials)
  produces 768-dimension retrieval embeddings for clinical notes, document
  chunks, and approved extraction output.
- **SQLite ``vector_chunks`` table** persists the vectors next to the rest of
  the tenant's clinical data, so the index survives restarts, rides the same
  Cloud Run volume mount, and stays tenant-isolated through
  ``database.tenant_storage``. In-process cosine similarity is exact and fast
  at this scale (hundreds to low thousands of chunks); a managed Vertex AI
  Vector Search endpoint would add provisioning latency and an always-on cost
  without improving results until the corpus is orders of magnitude larger.
- **Vertex AI Ranking API** (Discovery Engine ``semantic-ranker-default``)
  reranks the cosine candidates, which is exactly the "vector search plus
  reranker" retrieval shape. It degrades gracefully: any failure keeps the
  cosine ordering.

Every capability is best-effort: without credentials (unit tests, offline
demo) the store reports itself unavailable and callers fall back to the
deterministic keyword search that always worked.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

import requests

from . import database
from .config import get_config

logger = logging.getLogger("capstone_agent")

# DDL is also registered in clinical_schemas.SCHEMA_DDL for fresh databases;
# ensure_table() applies it to databases initialized before this module existed.
VECTOR_CHUNKS_DDL = """CREATE TABLE IF NOT EXISTS vector_chunks (
    chunk_id TEXT PRIMARY KEY,
    patient_id TEXT,
    source_type TEXT NOT NULL,
    source_id TEXT,
    chunk_text TEXT NOT NULL,
    embedding TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    created_at TEXT NOT NULL
)"""

_RANKING_ENDPOINT = (
    "https://discoveryengine.googleapis.com/v1/projects/{project}"
    "/locations/global/rankingConfigs/default_ranking_config:rank"
)

_EMBED_BATCH_SIZE = 20


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Exact cosine similarity between two equal-length vectors.

    Pure Python on purpose: the corpus is small enough that exact scoring
    beats approximate indexes, and it keeps the module dependency-free.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class VertexEmbeddingClient:
    """Vertex AI embedding calls through google-genai with ADC.

    No API key is read or stored here — authentication is Application
    Default Credentials locally and the service account on Cloud Run.
    """

    def __init__(self) -> None:
        """Read model selection and auth mode from central config."""
        config = get_config()
        self.model = config["embedding_model"]
        self.dimensions = config["embedding_dimensions"]
        self._enabled = config["enable_vector_search"] and config["gemini_enabled"]
        self._client: Any = None

    def available(self) -> bool:
        """Whether embedding calls can be attempted in this environment."""
        return self._enabled

    def _genai_client(self) -> Any:
        """Lazily build the google-genai client (Vertex first, API key fallback)."""
        if self._client is None:
            from google import genai

            config = get_config()
            if config["use_vertex_ai"] and config["gcp_project"]:
                self._client = genai.Client(
                    vertexai=True,
                    project=config["gcp_project"],
                    location=config["gcp_location"],
                )
            else:
                self._client = genai.Client(
                    api_key=config["google_api_key"], vertexai=False
                )
        return self._client

    def embed(
        self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[list[float]]:
        """Embed texts in batches; returns one vector per input text.

        Raises on failure — callers decide whether that means "fall back to
        keyword search" (queries) or "skip indexing" (ingestion).
        """
        client = self._genai_client()
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[start : start + _EMBED_BATCH_SIZE]
            response = client.models.embed_content(
                model=self.model,
                contents=batch,
                config={
                    "task_type": task_type,
                    "output_dimensionality": self.dimensions,
                },
            )
            vectors.extend([list(item.values) for item in response.embeddings])
        return vectors


class VertexReranker:
    """Semantic reranking via the Vertex AI Ranking API (Discovery Engine).

    Called over REST with an ADC bearer token so no extra client library is
    needed. Failures never break retrieval — the caller keeps cosine order.
    """

    def __init__(self) -> None:
        """Read reranker toggle and model from central config.

        Gated on a project id, not on Vertex mode: Cloud Run supplies ADC via
        its service account even when Gemini itself runs on the API-key path,
        and the rerank call fails soft to cosine order when ADC is absent.
        """
        config = get_config()
        self.model = config["reranker_model"]
        self._enabled = config["enable_reranker"] and bool(config["gcp_project"])

    def available(self) -> bool:
        """Whether reranking should be attempted in this environment."""
        return self._enabled

    def rerank(
        self, query: str, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]] | None:
        """Return records re-ordered by the Ranking API, or None on any failure.

        Each record must have ``chunk_id`` and ``text``; the returned records
        gain a ``rerank_score``.
        """
        if not self._enabled or not records:
            return None
        try:
            import google.auth
            import google.auth.transport.requests

            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(google.auth.transport.requests.Request())
            config = get_config()
            payload = {
                "model": self.model,
                "query": query[:1000],
                "records": [
                    {"id": str(index), "content": (record.get("text") or "")[:1500]}
                    for index, record in enumerate(records)
                ],
            }
            response = requests.post(
                _RANKING_ENDPOINT.format(project=config["gcp_project"]),
                headers={"Authorization": f"Bearer {credentials.token}"},
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            ranked = response.json().get("records", [])
            ordered: list[dict[str, Any]] = []
            for item in ranked:
                record = dict(records[int(item["id"])])
                record["rerank_score"] = float(item.get("score", 0.0))
                ordered.append(record)
            return ordered or None
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Reranker unavailable, keeping cosine order: %s", exc)
            return None


class ClinicalVectorStore:
    """Tenant-scoped semantic index persisted in the clinical SQLite store."""

    def __init__(
        self,
        db: database.DatabaseManager,
        embedder: VertexEmbeddingClient,
        reranker: VertexReranker,
    ) -> None:
        """Bind the store to the shared database manager and Vertex clients."""
        self._db = db
        self._embedder = embedder
        self._reranker = reranker
        self._backfilled_paths: set[str] = set()
        self._backfill_lock = threading.Lock()

    def available(self) -> bool:
        """Whether semantic indexing/search can run in this environment."""
        return self._embedder.available()

    def ensure_table(self, conn: sqlite3.Connection) -> None:
        """Create the vector_chunks table when missing (pre-existing databases)."""
        conn.execute(VECTOR_CHUNKS_DDL)

    def count(self) -> int:
        """Number of indexed chunks in the active tenant database."""
        self._db.init_db()
        with self._db.get_connection() as conn:
            self.ensure_table(conn)
            row = conn.execute("SELECT COUNT(*) AS n FROM vector_chunks").fetchone()
            return int(row["n"])

    def index_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Embed and upsert chunks; returns the number indexed.

        Each chunk dict needs ``chunk_id``, ``text``, and ``source_type``;
        ``patient_id`` and ``source_id`` are optional. Empty texts are skipped.
        """
        payload = [c for c in chunks if str(c.get("text") or "").strip()]
        if not payload or not self._embedder.available():
            return 0
        vectors = self._embedder.embed(
            [c["text"] for c in payload], task_type="RETRIEVAL_DOCUMENT"
        )
        now = datetime.now(timezone.utc).isoformat()
        self._db.init_db()
        with self._db.get_connection() as conn:
            self.ensure_table(conn)
            for chunk, vector in zip(payload, vectors):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO vector_chunks (
                        chunk_id, patient_id, source_type, source_id,
                        chunk_text, embedding, embedding_model, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(chunk["chunk_id"]),
                        chunk.get("patient_id") or None,
                        str(chunk.get("source_type", "document")),
                        chunk.get("source_id") or None,
                        str(chunk["text"])[:4000],
                        json.dumps(vector),
                        self._embedder.model,
                        now,
                    ),
                )
            conn.commit()
        return len(payload)

    def semantic_search(
        self, query: str, patient_id: str = "", limit: int = 8, rerank: bool = True
    ) -> list[dict[str, Any]]:
        """Cosine search over the index, optionally reranked by Vertex Ranking.

        Returns [] when embeddings are unavailable or the index is empty so
        callers can fall back to deterministic keyword retrieval.
        """
        if not self._embedder.available():
            return []
        if self.count() == 0:
            self.backfill_from_clinical_store()
            if self.count() == 0:
                return []
        try:
            query_vector = self._embedder.embed([query], task_type="RETRIEVAL_QUERY")[0]
        except Exception as exc:
            logger.warning(
                "Query embedding failed, falling back to keyword search: %s", exc
            )
            return []
        self._db.init_db()
        with self._db.get_connection() as conn:
            self.ensure_table(conn)
            if patient_id:
                rows = conn.execute(
                    "SELECT chunk_id, patient_id, source_type, source_id, chunk_text, embedding "
                    "FROM vector_chunks WHERE patient_id = ? OR patient_id IS NULL",
                    (patient_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT chunk_id, patient_id, source_type, source_id, chunk_text, embedding FROM vector_chunks"
                ).fetchall()
        scored: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                vector = json.loads(item.pop("embedding"))
            except (json.JSONDecodeError, TypeError):
                continue
            scored.append(
                {
                    "chunk_id": item["chunk_id"],
                    "patient_id": item["patient_id"],
                    "source_type": item["source_type"],
                    "source_id": item["source_id"],
                    "text": item["chunk_text"],
                    "relevance_score": round(
                        _cosine_similarity(query_vector, vector), 4
                    ),
                    "retrieval": "vector",
                }
            )
        scored.sort(key=lambda item: item["relevance_score"], reverse=True)
        candidates = scored[: max(limit * 3, limit)]
        if rerank and candidates:
            reranked = self._reranker.rerank(query, candidates)
            if reranked is not None:
                for item in reranked:
                    item["retrieval"] = "vector+rerank"
                return reranked[:limit]
        return candidates[:limit]

    def backfill_from_clinical_store(self, limit: int = 400) -> dict[str, Any]:
        """Index existing clinical notes, document chunks, and extractions.

        Runs at most once per tenant database per process (guarded), in
        bounded batches, so the first semantic query on a freshly mounted
        tenant self-heals its index without an operator step.
        """
        path_key = str(self._db.active_db_path())
        with self._backfill_lock:
            if path_key in self._backfilled_paths or not self._embedder.available():
                return {"indexed": 0, "skipped": True}
            self._backfilled_paths.add(path_key)
        self._db.init_db()
        chunks: list[dict[str, Any]] = []
        with self._db.get_connection() as conn:
            self.ensure_table(conn)
            already = {
                row["chunk_id"]
                for row in conn.execute("SELECT chunk_id FROM vector_chunks").fetchall()
            }
            for row in conn.execute(
                "SELECT note_id, patient_id, note_type, note_text FROM clinical_notes LIMIT ?",
                (limit,),
            ).fetchall():
                chunk_id = f"note-{row['note_id']}"
                if chunk_id not in already:
                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "patient_id": row["patient_id"],
                            "source_type": "clinical_note",
                            "source_id": row["note_id"],
                            "text": f"{row['note_type']}: {row['note_text']}",
                        }
                    )
            for row in conn.execute(
                "SELECT chunk_id, document_id, patient_id, chunk_text FROM document_chunks LIMIT ?",
                (limit,),
            ).fetchall():
                chunk_id = f"doc-{row['document_id']}-{row['chunk_id']}"
                if chunk_id not in already:
                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "patient_id": row["patient_id"],
                            "source_type": "document",
                            "source_id": row["document_id"],
                            "text": row["chunk_text"],
                        }
                    )
            field_rows = conn.execute(
                "SELECT session_id, patient_id, field_name, field_value FROM extracted_fields LIMIT ?",
                (limit,),
            ).fetchall()
        by_session: dict[str, dict[str, Any]] = {}
        for row in field_rows:
            entry = by_session.setdefault(
                row["session_id"],
                {"patient_id": row["patient_id"], "lines": []},
            )
            entry["lines"].append(f"{row['field_name']}: {row['field_value']}")
        for session_id, entry in by_session.items():
            chunk_id = f"ext-{session_id}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "patient_id": entry["patient_id"],
                    "source_type": "structured",
                    "source_id": session_id,
                    "text": "Extracted clinical fields. "
                    + "; ".join(entry["lines"][:40]),
                }
            )
        chunks = chunks[:limit]
        try:
            indexed = self.index_chunks(chunks)
        except Exception as exc:
            logger.warning(
                "Vector backfill failed (keyword search still available): %s", exc
            )
            return {"indexed": 0, "error": str(exc)}
        logger.info(
            "Vector index backfill complete: %s chunks embedded into %s",
            indexed,
            path_key,
        )
        return {"indexed": indexed, "candidates": len(chunks)}

    def status(self) -> dict[str, Any]:
        """Operational summary used by tools and the developer console."""
        return {
            "available": self.available(),
            "embedding_model": self._embedder.model,
            "dimensions": self._embedder.dimensions,
            "reranker": self._reranker.model
            if self._reranker.available()
            else "disabled",
            "indexed_chunks": self.count(),
            "database": str(self._db.active_db_path().name),
        }


# ---------------------------------------------------------------------------
# Module singletons and functional API (mirrors database.py's pattern).
# ---------------------------------------------------------------------------

embedder = VertexEmbeddingClient()
reranker = VertexReranker()
store = ClinicalVectorStore(database.manager, embedder, reranker)

semantic_search = store.semantic_search
index_chunks = store.index_chunks
backfill_vector_index = store.backfill_from_clinical_store
vector_index_status = store.status
