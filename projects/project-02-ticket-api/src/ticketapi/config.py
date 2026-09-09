"""Configuration loaded once at startup, validated, and never re-read.

M2-L09 (env vars), M2-L19 (secrets).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    """Who a token identifies."""

    user_id: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings.

    `tokens` is repr=False so the credentials never appear in a log line,
    traceback or debugger inspection (M2-L19 section 5.2).
    """

    app_env: str
    log_level: str
    database_path: str
    tokens: dict[str, Principal] = field(repr=False, default_factory=dict)


def _parse_tokens(raw: str) -> dict[str, Principal]:
    """Parse "token:user:role,token:user:role" into a lookup table."""
    table: dict[str, Principal] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"API_TOKENS entry {entry!r} must be 'token:user_id:role'"
            )
        token, user_id, role = (p.strip() for p in parts)
        if role not in {"agent", "admin"}:
            raise ValueError(f"unknown role {role!r} in API_TOKENS")
        table[token] = Principal(user_id=user_id, role=role)
    return table


def load_settings() -> Settings:
    """Read configuration from the environment, failing fast and clearly."""
    raw_tokens = os.getenv("API_TOKENS", "").strip()
    if not raw_tokens:
        raise RuntimeError(
            "API_TOKENS is not set. Copy .env.example to .env and fill it in."
        )
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        database_path=os.getenv("DATABASE_PATH", "./tickets.db"),
        tokens=_parse_tokens(raw_tokens),
    )
