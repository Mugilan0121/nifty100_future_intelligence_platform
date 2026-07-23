"""
Shared pytest fixtures for API tests.

Sprint 6 - Day 42
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """TestClient wrapping the FastAPI app, shared across all API tests."""
    return TestClient(app)