"""Shared fixtures. No network, no real database file, no real tokens."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "API_TOKENS",
    "tok-alice:u-alice:agent,tok-bob:u-bob:agent,tok-admin:u-admin:admin",
)
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient with a fresh in-memory database per test."""
    from ticketapi.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def alice() -> dict[str, str]:
    return {"Authorization": "Bearer tok-alice"}


@pytest.fixture
def bob() -> dict[str, str]:
    return {"Authorization": "Bearer tok-bob"}


@pytest.fixture
def admin() -> dict[str, str]:
    return {"Authorization": "Bearer tok-admin"}


@pytest.fixture
def conn():
    from ticketapi import db

    connection = db.connect(":memory:")
    yield connection
    connection.close()
