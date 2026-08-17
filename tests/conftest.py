"""Pytest configuration and shared fixtures for agent evaluation.

Sets up the ADK runner with session service, memory service,
and test helpers for agent evaluation.
"""

import os
import uuid

# Unit and contract tests must never export spans to a real backend. Set this
# before importing the agent because observability initializes at import time.
os.environ["ENABLE_TRACING"] = "FALSE"

import pytest
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.genai import types

from capstone_agent.agent import root_agent
from capstone_agent.memory import create_memory_service, create_session_service

load_dotenv()

APP_NAME = "capstone_agent_test"
USER_ID = "test_user"


@pytest.fixture(autouse=True)
def _demo_execution_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests deterministic regardless of AGENT_EXECUTION_MODE in .env.

    Tests that exercise live mode opt back in with monkeypatch.setenv.
    """
    monkeypatch.delenv("AGENT_EXECUTION_MODE", raising=False)


@pytest.fixture
def session_service():
    """Fresh in-memory session service for each test."""
    return create_session_service()


@pytest.fixture
def memory_service():
    """Fresh in-memory memory service for each test."""
    return create_memory_service()


@pytest.fixture
def runner(session_service, memory_service):
    """ADK runner wired to the root agent, session, and memory services."""
    return Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )


@pytest.fixture
def session_id():
    """Unique session ID per test."""
    return f"test_session_{uuid.uuid4().hex[:8]}"


async def get_agent_response(
    runner: Runner, user_id: str, session_id: str, query: str
) -> str:
    """Send a query to the agent and return its final text response."""
    content = types.Content(
        role="user",
        parts=[types.Part(text=query)],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text or ""

    return response_text
