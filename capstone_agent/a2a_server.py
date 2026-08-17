"""Expose this agent over the Agent2Agent (A2A) protocol (Day 5a).

`to_a2a()` wraps the root agent in a Starlette/FastAPI ASGI app and
auto-generates an Agent Card at `/.well-known/agent-card.json`, so other
agents (in any language/framework) can discover and call this one as a
remote sub-agent.

Run it:
    uvicorn capstone_agent.a2a_server:app --host 0.0.0.0 --port 8001

Then point a consumer at the card (see orchestration.build_remote_a2a_agent):
    http://<host>:8001/.well-known/agent-card.json

Requires the A2A extra:  pip install "google-adk[a2a]"
The module-level `app` is built defensively so importing the package never
hard-fails when the extra is absent (it stays None and logs a hint).
"""

import logging

from .agent import root_agent
from .config import get_config

_logger = logging.getLogger("capstone_agent")


def build_a2a_app():
    """Build the ASGI app exposing root_agent over A2A (needs google-adk[a2a])."""
    from google.adk.a2a.utils.agent_to_a2a import to_a2a  # lazy: needs a2a extra

    return to_a2a(root_agent, port=get_config()["a2a_port"])


try:
    app = build_a2a_app()
except Exception as _exc:  # pragma: no cover - depends on optional extra
    app = None
    _logger.warning(
        "A2A server unavailable; install the A2A extra to enable it "
        '(pip install "google-adk[a2a]"). Reason: %s',
        _exc,
    )
