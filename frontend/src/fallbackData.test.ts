import { describe, expect, it } from "vitest";
import { fallbackCatalog } from "./fallbackData";

describe("fallback agent catalog", () => {
  it("matches the implemented 21-specialist topology", () => {
    expect(Object.fromEntries(fallbackCatalog.pipelines.map(pipeline => [pipeline.id, pipeline.agents]))).toEqual({
      extraction: [
        "quality_assessor_agent",
        "ocr_processor_agent",
        "vision_analyzer_agent",
        "clinical_structuring_agent",
        "extraction_critic_agent",
        "extraction_refiner_agent",
        "clinical_review_request_agent",
      ],
      qa: [
        "qa_request_validation_agent",
        "context_assembly_agent",
        "evidence_retrieval_agent",
        "image_evidence_agent",
        "citation_builder_agent",
        "answer_synthesis_agent",
        "qa_audit_agent",
        "qa_response_agent",
      ],
      database: [
        "schema_discovery_agent",
        "nl_to_sql_agent",
        "sql_validator_agent",
        "sql_preview_approval_agent",
        "query_executor_agent",
        "insight_chart_agent",
      ],
    });
    expect(fallbackCatalog.pipelines.flatMap(pipeline => pipeline.agents)).toHaveLength(21);
  });
});
