import os
from dataclasses import dataclass
from functools import lru_cache


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or default


@dataclass(frozen=True)
class Settings:
    judit_requests_base_url: str
    judit_api_key: str | None
    anthropic_api_key: str | None
    claude_model: str
    request_timeout_seconds: float
    judit_poll_interval_seconds: float
    prompt_version: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        judit_requests_base_url=(
            _env("JUDIT_REQUESTS_BASE_URL") or "https://requests.production.judit.io"
        ).rstrip("/"),
        judit_api_key=_env("JUDIT_API_KEY"),
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        claude_model=_env("CLAUDE_MODEL", "claude-3-5-sonnet-20241022") or "claude-3-5-sonnet-20241022",
        request_timeout_seconds=float(_env("REQUEST_TIMEOUT_SECONDS", "30") or "30"),
        judit_poll_interval_seconds=float(_env("JUDIT_POLL_INTERVAL_SECONDS", "2") or "2"),
        prompt_version="summary-v1",
    )
