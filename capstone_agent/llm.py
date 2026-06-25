"""Model registry and factory — the one place model selection happens.

Day 1a idiom: never pass a bare model-id string to an agent. Wrap the model
in ADK's `Gemini` object configured with `HttpRetryOptions`, so transient
429/5xx errors are retried with exponential backoff instead of failing the run.

Three tiers are available (user-selectable AND orchestrated per-agent):

| Tier              | Model id                              | Use it for |
|-------------------|---------------------------------------|------------|
| `flash-lite`      | gemini-3.1-flash-lite                 | DEFAULT. Cheap, fast, high-frequency routing / simple tasks. |
| `pro`             | gemini-3.1-pro-preview                | Frontier reasoning for hard, multi-step sub-tasks. |
| `pro-customtools` | gemini-3.1-pro-preview-customtools    | Tool-heavy agents — Google's dedicated tool-calling variant; most reliable function calling. |

How the "switch" works:
- Global default: set `MODEL_TIER` (and optionally `MODEL_ID`) in `.env`.
- Per-agent orchestration: call `build_model(tier="pro")` for the agent that
  needs it. This is how the harness routes cheap models for coordination and
  expensive models only where they earn their cost (see agent.py).

>>> CUSTOMIZE: when you pick your capstone, choose a tier per agent here or in
    agent.py — no other code needs to change to swap models.
"""

from google.adk.models.google_llm import Gemini
from google.genai import types

from .config import get_config

# Registry of supported model tiers → concrete model ids (verified June 2026).
# The `-preview` Flash-Lite variant was retired May 2026, so we pin the GA id.
MODEL_TIERS: dict[str, str] = {
    "flash-lite": "gemini-3.1-flash-lite",
    "pro": "gemini-3.1-pro-preview",
    "pro-customtools": "gemini-3.1-pro-preview-customtools",
}

DEFAULT_TIER = "flash-lite"


def _retry_options() -> types.HttpRetryOptions:
    """Exponential-backoff retry policy applied to every model (Day 1a).

    Retries the transient, retryable HTTP statuses (rate limit + server
    errors). Non-retryable 4xx (e.g. 400/401/403) fail fast as they should.
    """
    return types.HttpRetryOptions(
        attempts=5,
        initial_delay=1,
        max_delay=60,
        exp_base=2,
        http_status_codes=[429, 500, 502, 503, 504],
    )


def resolve_model_id(tier: str | None = None) -> str:
    """Resolve a tier name (or raw model id) to a concrete model id.

    - `tier=None` → the configured default tier (`MODEL_TIER`).
    - A known tier name → its mapped model id.
    - An unknown string → returned as-is (lets callers pass a raw model id).
    - For the default tier, an explicit `MODEL_ID` in `.env` wins, so power
      users can pin a specific model without editing code.
    """
    config = get_config()
    tier = tier or config["model_tier"] or DEFAULT_TIER

    # Explicit MODEL_ID override only applies to the configured default tier.
    if tier == config["model_tier"] and config.get("model_id"):
        return config["model_id"]

    return MODEL_TIERS.get(tier, tier)


def build_model(tier: str | None = None) -> Gemini:
    """Return a configured `Gemini` model for the given tier.

    This is the factory every agent should use instead of a bare string,
    so retry behaviour and tier resolution stay centralized and consistent.

    Example:
        root = LlmAgent(model=build_model(), ...)            # default tier
        deep = LlmAgent(model=build_model("pro"), ...)       # reasoning
        tooled = LlmAgent(model=build_model("pro-customtools"), ...)
    """
    return Gemini(model=resolve_model_id(tier), retry_options=_retry_options())
