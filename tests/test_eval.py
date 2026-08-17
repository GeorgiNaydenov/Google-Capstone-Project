"""ADK evaluation harness test (Day 4b).

Runs the agent against eval/capstone.evalset.json using ADK's AgentEvaluator,
scoring against the criteria in eval/test_config.json (auto-discovered from the
eval directory). This is a *live* eval — it invokes the model — so it is skipped
unless Gemini credentials (API key or Vertex AI project) are set.

Run just this:  pytest tests/test_eval.py -v
Or via the CLI:  adk eval capstone_agent eval/capstone.evalset.json \
                     --config_file_path eval/test_config.json --print_detailed_results
"""

import importlib.util
import json
import os
from pathlib import Path

import pytest

_HAS_GEMINI = bool(
    os.getenv("GOOGLE_API_KEY")
    or (
        os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"
        and os.getenv("GOOGLE_CLOUD_PROJECT")
    )
)

pytestmark = [
    pytest.mark.requires_model,
    pytest.mark.skipif(
        not _HAS_GEMINI,
        reason="Gemini credentials (API key or Vertex AI project) required for live agent evaluation",
    ),
]


async def test_agent_meets_baseline_eval():
    from google.adk.evaluation import AgentEvaluator
    from google.adk.evaluation.eval_config import EvalConfig
    from google.adk.evaluation.eval_set import EvalSet

    if importlib.util.find_spec("pandas") is None:
        pytest.skip("pandas is required for google-adk evaluation")

    eval_dir = Path("eval")
    eval_set = EvalSet.model_validate_json(
        (eval_dir / "capstone.evalset.json").read_text(encoding="utf-8")
    )
    eval_config = EvalConfig.model_validate(
        json.loads((eval_dir / "test_config.json").read_text(encoding="utf-8"))
    )

    # Evaluate cases serially. Parallel cases can contend for the same local
    # MCP subprocess and turn an application-quality signal into a transport
    # timeout, especially on Windows and constrained CI runners.
    requested_case = os.getenv("EVAL_CASE_ID")
    eval_cases = [
        case
        for case in eval_set.eval_cases
        if requested_case is None or case.eval_id == requested_case
    ]
    if requested_case and not eval_cases:
        pytest.fail(f"Unknown EVAL_CASE_ID: {requested_case}")

    for eval_case in eval_cases:
        await AgentEvaluator.evaluate_eval_set(
            agent_module="capstone_agent",
            eval_set=eval_set.model_copy(update={"eval_cases": [eval_case]}),
            eval_config=eval_config,
            num_runs=1,
            print_detailed_results=True,
        )
