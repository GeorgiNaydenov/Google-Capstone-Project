"""Tests for the orchestration building blocks (Day 1b / 2a).

Construction-only tests — they verify the workflow primitives are wired
correctly (sub-agent order, output_key plumbing, loop bounds) without calling
the LLM, so they run with no API key.
"""

from types import SimpleNamespace

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent
from google.adk.tools import AgentTool

from capstone_agent import orchestration as orch


def test_writing_pipeline_is_ordered_with_state_plumbing():
    pipeline = orch.build_writing_pipeline()
    assert isinstance(pipeline, SequentialAgent)
    assert [a.name for a in pipeline.sub_agents] == ["outliner", "writer", "editor"]
    # Each stage writes its result to session state via output_key (Day 1b).
    assert pipeline.sub_agents[0].output_key == "outline"
    assert pipeline.sub_agents[1].output_key == "draft"


def test_parallel_research_fans_out_then_aggregates():
    system = orch.build_parallel_research(("alpha", "beta"))
    assert isinstance(system, SequentialAgent)
    fan_out, aggregator = system.sub_agents
    assert isinstance(fan_out, ParallelAgent)
    assert len(fan_out.sub_agents) == 2
    assert aggregator.name == "aggregator"


def test_refinement_loop_respects_max_iterations():
    loop = orch.build_refinement_loop(max_iterations=2)
    assert isinstance(loop, LoopAgent)
    assert loop.max_iterations == 2
    assert [a.name for a in loop.sub_agents] == ["critic", "refiner"]


def test_as_tool_wraps_agent_as_callable_tool():
    tool = orch.as_tool(orch.build_code_executor_agent())
    assert isinstance(tool, AgentTool)


def test_code_executor_agent_has_executor():
    agent = orch.build_code_executor_agent()
    assert agent.code_executor is not None


def test_exit_loop_signals_escalation():
    ctx = SimpleNamespace(actions=SimpleNamespace(escalate=False))
    result = orch.exit_loop(ctx)
    assert ctx.actions.escalate is True
    assert result["status"] == "success"


def test_sql_draft_agent_is_single_stage_with_inline_schema():
    agent = orch.build_sql_draft_agent()
    # The product preview reads this state key via live_bridge's
    # _STATE_OUTPUT_KEYS, same as the full pipeline's nl_to_sql stage.
    assert agent.output_key == "generated_sql"
    # No tools: the draft is one model call; safety validation and execution
    # happen deterministically server-side.
    assert not agent.tools
    # Schema is inlined at build time so the model never guesses columns.
    assert "patients_core" in agent.instruction
    assert "__SCHEMA_DDL__" not in agent.instruction
    # Runs as its own Runner root, so it must carry security layers 1 and 3.
    assert agent.before_model_callback is not None
    assert agent.after_model_callback is not None
