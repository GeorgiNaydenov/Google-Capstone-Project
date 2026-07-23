"""ADK `App` wrapper — the richer runtime around the root agent.

`root_agent` (agent.py) stays the entry point for `adk run` / `adk web`. This
`App` bundles the production runtime features the course adds on top:

- plugins              — observability + logging across the lifecycle (Day 4a)
- EventsCompactionConfig — automatic history compaction so long conversations
  stay within budget without manual truncation (Day 3a). This is ADK's native
  replacement for the rule-based context.compact_history fallback.
- ResumabilityConfig   — pause/resume so human-in-the-loop long-running tools
  can suspend a run and continue after a human decision (Day 2b).

Use `build_app()` for programmatic runners (tests, A2A serving, resumable HITL
flows). Example:

    from capstone_agent.app import build_app
    from capstone_agent.memory import create_session_service
    runner = Runner(app=build_app(), session_service=create_session_service())
"""

from google.adk.apps.app import App, EventsCompactionConfig, ResumabilityConfig

from .agent import root_agent
from .config import get_config
from .plugins import build_plugins


def build_app() -> App:
    """Construct the App with plugins, compaction, and resumability."""
    config = get_config()
    return App(
        name=config["app_name"],
        root_agent=root_agent,
        # Day 4a: lifecycle observability (redacted) + verbose request tracing.
        plugins=build_plugins(),
        # Day 3a: summarize history every N events, keeping `overlap_size`
        # recent events verbatim for continuity.
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=config["session_compact_after"],
            overlap_size=5,
        ),
        # Day 2b: required for the human-in-the-loop approval pause/resume.
        resumability_config=ResumabilityConfig(
            is_resumable=config["enable_resumability"]
        ),
    )


# Convenience module-level instance for runners/tests that just want `app`.
app = build_app()
