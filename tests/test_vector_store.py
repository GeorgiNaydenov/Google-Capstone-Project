"""Unit tests for the semantic vector store (capstone_agent/vector_store.py).

Pure-function and contract coverage — no network, no credentials. Embeddings
are stubbed so the store's indexing, cosine ranking, tenant isolation, and
keyword-fallback contracts are asserted deterministically.
"""

from pathlib import Path

from capstone_agent import database, vector_store
from capstone_agent.vector_store import ClinicalVectorStore, _cosine_similarity


class StubEmbedder:
    """Deterministic 3-dimension embedder keyed on clinical keywords."""

    model = "stub-embedding"
    dimensions = 3

    def available(self) -> bool:
        return True

    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([
                1.0 if "hepatic" in lowered or "liver" in lowered else 0.0,
                1.0 if "cardiac" in lowered or "heart" in lowered else 0.0,
                1.0,
            ])
        return vectors


class OfflineEmbedder(StubEmbedder):
    """Embedder that reports itself unavailable (no credentials)."""

    def available(self) -> bool:
        return False


class StubReranker:
    """Reranker that is disabled, exercising the cosine-order path."""

    model = "stub-ranker"

    def available(self) -> bool:
        return False

    def rerank(self, query: str, records: list[dict]) -> None:
        return None


class TestCosineSimilarity:
    """_cosine_similarity must behave like the textbook definition."""

    def test_identical_vectors_score_one(self) -> None:
        assert _cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0

    def test_orthogonal_vectors_score_zero(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_zero_vector_scores_zero(self) -> None:
        assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


class TestClinicalVectorStore:
    """Index round-trip, patient scoping, and unavailability contracts."""

    def _store(self, embedder=None) -> ClinicalVectorStore:
        return ClinicalVectorStore(database.manager, embedder or StubEmbedder(), StubReranker())

    def test_index_and_semantic_search_round_trip(self, tmp_path: Path) -> None:
        with database.tenant_storage(tmp_path / "vec.db", tmp_path / "uploads"):
            store = self._store()
            indexed = store.index_chunks([
                {"chunk_id": "c1", "patient_id": "PT-1", "source_type": "clinical_note",
                 "text": "Hepatic lesion increased in size on follow-up CT."},
                {"chunk_id": "c2", "patient_id": "PT-1", "source_type": "clinical_note",
                 "text": "Cardiac exam unremarkable, regular rate and rhythm."},
            ])
            assert indexed == 2
            assert store.count() == 2

            results = store.semantic_search("liver tumor progression", patient_id="PT-1", rerank=False)
            assert results[0]["chunk_id"] == "c1"
            assert results[0]["retrieval"] == "vector"
            assert results[0]["relevance_score"] > results[1]["relevance_score"]

    def test_patient_scoping_excludes_other_patients(self, tmp_path: Path) -> None:
        with database.tenant_storage(tmp_path / "vec.db", tmp_path / "uploads"):
            store = self._store()
            store.index_chunks([
                {"chunk_id": "mine", "patient_id": "PT-1", "source_type": "document", "text": "hepatic mass"},
                {"chunk_id": "other", "patient_id": "PT-2", "source_type": "document", "text": "hepatic cyst"},
            ])
            results = store.semantic_search("liver finding", patient_id="PT-1", rerank=False)
            assert {item["chunk_id"] for item in results} == {"mine"}

    def test_unavailable_embedder_returns_empty_for_fallback(self, tmp_path: Path) -> None:
        with database.tenant_storage(tmp_path / "vec.db", tmp_path / "uploads"):
            store = self._store(OfflineEmbedder())
            assert store.semantic_search("anything") == []
            assert store.index_chunks([{"chunk_id": "x", "source_type": "document", "text": "t"}]) == 0

    def test_backfill_skips_when_unavailable(self, tmp_path: Path) -> None:
        with database.tenant_storage(tmp_path / "vec.db", tmp_path / "uploads"):
            store = self._store(OfflineEmbedder())
            assert store.backfill_from_clinical_store()["indexed"] == 0

    def test_upsert_replaces_same_chunk_id(self, tmp_path: Path) -> None:
        with database.tenant_storage(tmp_path / "vec.db", tmp_path / "uploads"):
            store = self._store()
            store.index_chunks([{"chunk_id": "c1", "source_type": "document", "text": "hepatic v1"}])
            store.index_chunks([{"chunk_id": "c1", "source_type": "document", "text": "hepatic v2"}])
            assert store.count() == 1


class TestToolFallback:
    """search_vector_store keeps working without semantic availability."""

    def test_tool_reports_keyword_mode_when_semantic_unavailable(self, monkeypatch) -> None:
        from capstone_agent import tools

        monkeypatch.setattr(vector_store.store._embedder, "_enabled", False)
        result = tools.search_vector_store("diabetes follow up", "PT-1044")
        assert result["status"] == "success"
        assert result["data"]["retrieval_mode"] == "keyword"
