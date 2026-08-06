"""Phase 3 settings tests (spec §2, corrected C3/C4).

- ``GEMINI_DATA_POLICY`` is Literal-validated — an invalid deployment value
  fails at startup (Pydantic ValidationError), never silent fall-through.
- ``AI_MAX_CONTEXT_TOKENS`` is the total context budget; the reserved output
  allowance is a separate setting (C4 rename).
- ``has_ai`` is True only when a Gemini key is configured.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.config import Settings


def test_invalid_gemini_data_policy_fails_fast() -> None:
    with pytest.raises(ValidationError):
        Settings(
            api_session_secret="x",
            environment="test",
            gemini_data_policy="not-a-real-policy",
        )


@pytest.mark.parametrize("policy", ["local_free", "client_paid", "disabled"])
def test_valid_gemini_data_policies_accepted(policy: str) -> None:
    settings = Settings(
        api_session_secret="x",
        environment="test",
        gemini_data_policy=policy,
    )
    assert settings.gemini_data_policy == policy


def test_ai_context_tokens_is_total_context_budget() -> None:
    settings = Settings(
        api_session_secret="x",
        environment="test",
        ai_max_context_tokens=24_000,
        ai_reserved_output_tokens=4_096,
    )
    assert settings.ai_max_context_tokens == 24_000
    assert settings.ai_reserved_output_tokens == 4_096
    # Effective input allowance is the difference (C4 semantics).
    assert settings.ai_max_context_tokens - settings.ai_reserved_output_tokens == 19_904


def test_has_ai_false_without_key() -> None:
    settings = Settings(api_session_secret="x", environment="test", gemini_api_key=None)
    assert settings.has_ai is False


def test_has_ai_true_with_key() -> None:
    settings = Settings(
        api_session_secret="x",
        environment="test",
        gemini_api_key="fake-key-for-settings-test",
    )
    assert settings.has_ai is True


def test_queue_wait_seconds_default() -> None:
    settings = Settings(api_session_secret="x", environment="test")
    assert settings.ai_queue_wait_seconds == 30
