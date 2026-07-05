"""Multi-agent orchestration building blocks (Day 1b, 2a, 5a).

This module provides reusable composition patterns plus three clinical
pipeline factories for the Clinical AI Command Center.

Generic patterns (from the course):
- Sequential pipeline, Parallel fan-out, Refinement loop
- Agent-as-tool, Code executor, Remote A2A agent

Clinical pipelines:
- Image Extraction Pipeline (SequentialAgent + LoopAgent validation)
- Patient Q&A Pipeline (SequentialAgent with 6 stages)
- DB Intelligence Pipeline (SequentialAgent with 5 stages)

Each pipeline uses output_key for inter-stage state plumbing and
per-agent model tier selection for cost/capability balancing.
"""

from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import AgentTool, load_memory
from google.adk.tools.tool_context import ToolContext

from .llm import build_model
from .memory import search_past_conversations
from .prompts import CLINICAL_INSTRUCTIONS
from .tools import (
    # Document tools
    upload_document,
    search_documents,
    list_uploaded_documents,
    # Image extraction
    assess_image_quality,
    extract_clinical_text,
    analyze_clinical_image,
    structure_clinical_findings,
    store_to_gcs,
    flag_for_review,
    transition_extraction_review,
    persist_extraction_relational,
    persist_extraction_vector,
    # Patient Q&A
    lookup_patient_record,
    validate_qa_request,
    search_clinical_notes,
    search_vector_store,
    retrieve_imaging_evidence,
    fetch_image_from_gcs,
    analyze_evidence_images,
    build_citations,
    compose_clinical_answer,
    save_qa_to_memory,
    # DB Intelligence
    get_database_schema,
    generate_sql,
    validate_sql_safety,
    approve_sql_preview,
    execute_approved_clinical_query,
    generate_chart_spec,
    generate_clinical_visual,
    save_query_to_memory,
    # Shared
    log_audit_event,
)


# ---------------------------------------------------------------------------
# Agent-as-tool (Day 2a): coordinator CALLS the specialist and keeps control.
# Contrast with sub_agents=[...] which TRANSFERS control to the specialist.
# ---------------------------------------------------------------------------
def as_tool(agent: LlmAgent) -> AgentTool:
    """Wrap an agent so it can be used as a callable tool by another agent."""
    return AgentTool(agent=agent)


# ---------------------------------------------------------------------------
# Loop control (Day 1b): a FunctionTool that signals a LoopAgent to stop.
# ---------------------------------------------------------------------------
def exit_loop(tool_context: ToolContext) -> dict:
    """Stop the surrounding refinement loop because the work is good enough.

    Call this from inside a LoopAgent stage when no further iteration is
    needed. It sets the ADK escalate signal, which ends the loop early.

    Returns:
        A small status dict (the loop terminates regardless).
    """
    tool_context.actions.escalate = True
    return {"status": "success", "message": "Quality bar met; stopping loop."}


# ============================================================================
# CLINICAL PIPELINE 1: Image Extraction
# ============================================================================

def build_image_extraction_pipeline() -> SequentialAgent:
    """Build extraction with OCR, review, persistence, and audit stages.

    Pipeline: quality_assessor → vision_analyzer → clinical_structurer
              → validation_gate (loop: critic ↔ refiner)

    Each stage reads from the prior stage's output_key via {state} injection.
    Model tiers: flash-lite for cheap stages, pro-customtools for vision,
    pro for clinical structuring.
    """
    quality_assessor = LlmAgent(
        model=build_model("flash-lite"),
        name="quality_assessor_agent",
        description="Checks clinical image quality before analysis.",
        instruction=CLINICAL_INSTRUCTIONS["quality_assessor"],
        tools=[assess_image_quality],
        output_key="quality_report",
    )

    ocr_processor = LlmAgent(
        model=build_model("flash-lite"),
        name="ocr_processor_agent",
        description="Extracts clinical text and metadata before vision analysis.",
        instruction=CLINICAL_INSTRUCTIONS["ocr_processor"],
        tools=[extract_clinical_text],
        output_key="ocr_output",
    )

    vision_analyzer = LlmAgent(
        model=build_model("pro-customtools"),
        name="vision_analyzer_agent",
        description="Analyzes clinical images using Gemini multimodal vision.",
        instruction=CLINICAL_INSTRUCTIONS["vision_analyzer"],
        tools=[analyze_clinical_image],
        output_key="vision_findings",
    )

    clinical_structurer = LlmAgent(
        model=build_model("pro"),
        name="clinical_structuring_agent",
        description="Maps vision findings to ontology codes with confidence scores.",
        instruction=CLINICAL_INSTRUCTIONS["clinical_structurer"],
        tools=[structure_clinical_findings, store_to_gcs],
        output_key="structured_output",
    )

    # Validation gate: LoopAgent with critic + refiner
    critic = LlmAgent(
        model=build_model("flash-lite"),
        name="extraction_critic_agent",
        description="Validates extraction quality and confidence thresholds.",
        instruction=CLINICAL_INSTRUCTIONS["extraction_critic"],
        tools=[exit_loop],
        output_key="critique",
    )

    refiner = LlmAgent(
        model=build_model("flash-lite"),
        name="extraction_refiner_agent",
        description="Flags low-confidence fields for human review.",
        instruction=CLINICAL_INSTRUCTIONS["extraction_refiner"],
        tools=[flag_for_review],
        output_key="refined_output",
    )

    validation_gate = LoopAgent(
        name="validation_gate",
        sub_agents=[critic, refiner],
        max_iterations=2,
    )

    review_gate = LlmAgent(
        model=build_model("flash-lite"),
        name="clinical_review_gate_agent",
        description="Applies explicit clinician approval or rejection.",
        instruction=CLINICAL_INSTRUCTIONS["clinical_review_gate"],
        tools=[transition_extraction_review],
        output_key="review_decision",
    )

    persistence = LlmAgent(
        model=build_model("flash-lite"),
        name="extraction_persistence_agent",
        description="Persists approved extraction to relational and vector stores.",
        instruction=CLINICAL_INSTRUCTIONS["extraction_persistence"],
        tools=[store_to_gcs, persist_extraction_relational, persist_extraction_vector],
        output_key="persistence_receipts",
    )

    extraction_audit = LlmAgent(
        model=build_model("flash-lite"),
        name="extraction_audit_agent",
        description="Records review and persistence receipts in the audit trail.",
        instruction=CLINICAL_INSTRUCTIONS["extraction_audit"],
        tools=[log_audit_event],
        output_key="extraction_audit_receipt",
    )

    return SequentialAgent(
        name="image_extraction_pipeline",
        description=(
            "Extracts structured clinical data from medical images. "
            "Runs quality, OCR, vision, structuring, clinician review, "
            "approved persistence, and audit stages."
        ),
        sub_agents=[
            quality_assessor,
            ocr_processor,
            vision_analyzer,
            clinical_structurer,
            validation_gate,
            review_gate,
            persistence,
            extraction_audit,
        ],
    )


# ============================================================================
# CLINICAL PIPELINE 2: Patient Q&A
# ============================================================================

def build_patient_qa_pipeline() -> SequentialAgent:
    """Build the patient Q&A pipeline (6 agents, sequential).

    Pipeline: context_assembly → evidence_retrieval → image_evidence
              → citation_builder → answer_synthesis → qa_audit

    Handles multi-image retrieval and comparison. Uses all 4 memory layers:
    - Layer 1: context.py working memory for each agent call
    - Layer 2: session.state via output_key plumbing
    - Layer 3: load_memory + search_past_conversations for cross-session recall
    - Layer 4: A2A context isolation for delegated calls
    """
    request_validation = LlmAgent(
        model=build_model("flash-lite"),
        name="qa_request_validation_agent",
        description="Validates patient scope and evidence filters.",
        instruction=CLINICAL_INSTRUCTIONS["qa_request_validation"],
        tools=[validate_qa_request],
        output_key="validated_qa_request",
    )

    context_assembly = LlmAgent(
        model=build_model("flash-lite"),
        name="context_assembly_agent",
        description="Assembles patient context from records and memory.",
        instruction=CLINICAL_INSTRUCTIONS["context_assembly"],
        tools=[lookup_patient_record, load_memory, search_past_conversations],
        output_key="patient_context",
    )

    evidence_retrieval = LlmAgent(
        model=build_model("pro-customtools"),
        name="evidence_retrieval_agent",
        description="Retrieves text and image evidence from database and vector search.",
        instruction=CLINICAL_INSTRUCTIONS["evidence_retrieval"],
        tools=[search_clinical_notes, search_vector_store, search_documents, retrieve_imaging_evidence],
        output_key="retrieved_evidence",
    )

    image_evidence = LlmAgent(
        model=build_model("pro-customtools"),
        name="image_evidence_agent",
        description="Analyzes retrieved images using Gemini vision.",
        instruction=CLINICAL_INSTRUCTIONS["image_evidence"],
        tools=[fetch_image_from_gcs, analyze_evidence_images],
        output_key="image_analysis",
    )

    citation_builder = LlmAgent(
        model=build_model("flash-lite"),
        name="citation_builder_agent",
        description="Builds numbered citations from evidence sources.",
        instruction=CLINICAL_INSTRUCTIONS["citation_builder"],
        tools=[build_citations],
        output_key="cited_sources",
    )

    answer_synthesis = LlmAgent(
        model=build_model("pro"),
        name="answer_synthesis_agent",
        description="Synthesizes cited clinical answers with image references.",
        instruction=CLINICAL_INSTRUCTIONS["answer_synthesis"],
        tools=[compose_clinical_answer, generate_clinical_visual],
        output_key="qa_answer",
    )

    qa_audit = LlmAgent(
        model=build_model("flash-lite"),
        name="qa_audit_agent",
        description="Logs Q&A interactions and saves findings to memory.",
        instruction=CLINICAL_INSTRUCTIONS["qa_audit"],
        tools=[log_audit_event, save_qa_to_memory],
        output_key="qa_audit_event",
    )

    return SequentialAgent(
        name="patient_qa_pipeline",
        description=(
            "Answers clinical questions about specific patients using "
            "structured records, vectorized notes, and image evidence. "
            "Returns cited answers with inline image references."
        ),
        sub_agents=[
            request_validation, context_assembly, evidence_retrieval, image_evidence,
            citation_builder, answer_synthesis, qa_audit,
        ],
    )


# ============================================================================
# CLINICAL PIPELINE 3: DB Intelligence
# ============================================================================

def build_db_intelligence_pipeline() -> SequentialAgent:
    """Build database intelligence with explicit preview approval.

    Pipeline: schema_discovery → nl_to_sql → sql_validator
              → query_executor (with code executor) → insight_chart

    Uses memory Layer 3 to recall and reuse prior query patterns.
    The query_executor uses BuiltInCodeExecutor for data transformations.
    """
    schema_discovery = LlmAgent(
        model=build_model("flash-lite"),
        name="schema_discovery_agent",
        description="Discovers database schema for query generation.",
        instruction=CLINICAL_INSTRUCTIONS["schema_discovery"],
        tools=[get_database_schema, search_past_conversations],
        output_key="schema_context",
    )

    nl_to_sql = LlmAgent(
        model=build_model("pro"),
        name="nl_to_sql_agent",
        description="Translates natural language questions to SQL.",
        instruction=CLINICAL_INSTRUCTIONS["nl_to_sql"],
        tools=[generate_sql],
        output_key="generated_sql",
    )

    sql_validator = LlmAgent(
        model=build_model("flash-lite"),
        name="sql_validator_agent",
        description="Validates SQL for safety and correctness.",
        instruction=CLINICAL_INSTRUCTIONS["sql_validator"],
        tools=[validate_sql_safety],
        output_key="validated_sql",
    )

    sql_approval = LlmAgent(
        model=build_model("flash-lite"),
        name="sql_preview_approval_agent",
        description="Presents safe SQL and requires explicit approval before execution.",
        instruction=CLINICAL_INSTRUCTIONS["sql_preview_approval"],
        tools=[approve_sql_preview],
        output_key="sql_approval",
    )

    # No code_executor here: Gemini rejects mixing built-in code execution
    # with function declarations (AFC gets disabled and every tool call
    # fails in a retry loop). Code execution lives on the root agent's
    # code_executor_tool instead.
    query_executor = LlmAgent(
        model=build_model("flash-lite"),
        name="query_executor_agent",
        description="Executes validated SQL queries.",
        instruction=CLINICAL_INSTRUCTIONS["query_executor"],
        tools=[execute_approved_clinical_query],
        output_key="query_results",
    )

    insight_chart = LlmAgent(
        model=build_model("pro"),
        name="insight_chart_agent",
        description="Generates insights and charts from query results.",
        instruction=CLINICAL_INSTRUCTIONS["insight_chart"],
        tools=[generate_chart_spec, generate_clinical_visual, log_audit_event, save_query_to_memory],
        output_key="insight_summary",
    )

    return SequentialAgent(
        name="db_intelligence_pipeline",
        description=(
            "Answers data questions across the patient database. "
            "Generates SQL, validates safety, executes queries, "
            "and produces insights with chart specifications."
        ),
        sub_agents=[
            schema_discovery,
            nl_to_sql,
            sql_validator,
            sql_approval,
            query_executor,
            insight_chart,
        ],
    )


# ============================================================================
# GENERIC PATTERNS (from the course — kept as reference/reusable)
# ============================================================================

def build_writing_pipeline() -> SequentialAgent:
    """Three-stage assembly line where each stage builds on the previous one."""
    outliner = LlmAgent(
        model=build_model(),
        name="outliner",
        description="Produces a short outline for a topic.",
        instruction="Create a tight 3-bullet outline for the user's topic.",
        output_key="outline",
    )
    writer = LlmAgent(
        model=build_model(),
        name="writer",
        description="Writes a draft from an outline.",
        instruction="Write a concise draft based on this outline:\n{outline}",
        output_key="draft",
    )
    editor = LlmAgent(
        model=build_model("pro"),
        name="editor",
        description="Polishes a draft for clarity and correctness.",
        instruction="Polish this draft for clarity and flow:\n{draft}",
        output_key="final",
    )
    return SequentialAgent(name="writing_pipeline", sub_agents=[outliner, writer, editor])


def build_parallel_research(topics: tuple[str, ...] = ("technology", "health", "finance")) -> SequentialAgent:
    """Run one researcher per topic concurrently, then aggregate the findings."""
    researchers = [
        LlmAgent(
            model=build_model(),
            name=f"researcher_{i}",
            description=f"Researches the {topic} angle.",
            instruction=f"Research the user's request from a {topic} perspective. Be brief.",
            output_key=f"research_{i}",
        )
        for i, topic in enumerate(topics)
    ]
    fan_out = ParallelAgent(name="parallel_research", sub_agents=researchers)

    merge_keys = " ".join(f"{{research_{i}}}" for i in range(len(topics)))
    aggregator = LlmAgent(
        model=build_model("pro"),
        name="aggregator",
        description="Synthesizes parallel research into one answer.",
        instruction=f"Synthesize these findings into one coherent summary:\n{merge_keys}",
        output_key="summary",
    )
    return SequentialAgent(name="research_system", sub_agents=[fan_out, aggregator])


def build_refinement_loop(max_iterations: int = 3) -> LoopAgent:
    """Iteratively critique and improve a `{draft}` in session state."""
    critic = LlmAgent(
        model=build_model(),
        name="critic",
        description="Critiques the current draft.",
        instruction=(
            "Critique the current draft:\n{draft}\n"
            "If it is already high quality, call the exit_loop tool. "
            "Otherwise give one concrete improvement."
        ),
        tools=[exit_loop],
        output_key="critique",
    )
    refiner = LlmAgent(
        model=build_model(),
        name="refiner",
        description="Improves the draft using the critique.",
        instruction="Improve the draft:\n{draft}\nApply this critique:\n{critique}",
        output_key="draft",
    )
    return LoopAgent(
        name="refinement_loop",
        sub_agents=[critic, refiner],
        max_iterations=max_iterations,
    )


# ---------------------------------------------------------------------------
# Code executor agent (Day 2a): runs generated Python for exact computation.
# ---------------------------------------------------------------------------
def build_code_executor_agent() -> LlmAgent:
    """An agent that solves precise math/data tasks by executing Python.

    Use `as_tool(build_code_executor_agent())` to give a coordinator a reliable
    calculator instead of trusting the LLM to do arithmetic in its head.
    """
    return LlmAgent(
        model=build_model(),
        name="code_executor_agent",
        description="Solves exact calculations by running Python code.",
        instruction=(
            "For any calculation, respond by writing and running Python code. "
            "Return only the computed result and a one-line explanation."
        ),
        code_executor=BuiltInCodeExecutor(),
    )


# ---------------------------------------------------------------------------
# Remote A2A agent (Day 5a): consume another agent over the network.
# Lazy import keeps the `a2a` extra optional until you actually use it.
# ---------------------------------------------------------------------------
def build_remote_a2a_agent(name: str, description: str, agent_card_url: str):
    """Wrap a remote agent (exposed via to_a2a) so it can be a sub-agent.

    Args:
        name: Local name for the remote agent.
        description: What the remote agent does (helps the parent route to it).
        agent_card_url: URL to the remote agent card, e.g.
            "http://host:8001/.well-known/agent-card.json".

    Requires the `a2a` extra: pip install "google-adk[a2a]".
    """
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent  # lazy

    return RemoteA2aAgent(name=name, description=description, agent_card=agent_card_url)
