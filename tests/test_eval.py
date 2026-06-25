"""ADK evaluation harness test (Day 4b).

Runs the agent against eval/capstone.evalset.json using ADK's AgentEvaluator,
scoring against the criteria in eval/test_config.json (auto-discovered from the
eval directory). This is a *live* eval — it invokes the model — so it is skipped
unless GOOGLE_API_KEY is set.

Run just this:  pytest tests/test_eval.py -v
Or via the CLI:  adk eval capstone_agent eval/capstone.evalset.json \
                     --config_file_path eval/test_config.json --print_detailed_results
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY required for live agent evaluation",
)


async def test_agent_meets_baseline_eval():
    from google.adk.evaluation import AgentEvaluator
    
    try:
        import pandas
    except ImportError:
        pytest.skip("pandas is required for google-adk evaluation")

    # evaluate() auto-discovers test_config.json next to the eval set.
    await AgentEvaluator.evaluate(
        agent_module="capstone_agent",
        eval_dataset_file_path_or_dir="eval/capstone.evalset.json",
        num_runs=1,
    )
