"""
GET /api/v1/health

Sprint 6 - Day 38
"""

import time

from fastapi import APIRouter

from src.api.db import get_table_row_counts

router = APIRouter(tags=["health"])

API_VERSION = "1.0.0"
_START_TIME = time.time()


@router.get("/health")
def health_check() -> dict:
    """Liveness/readiness check: DB row counts, uptime, and version."""
    return {
        "status": "ok",
        "db_row_counts": get_table_row_counts(),
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "version": API_VERSION,
    }