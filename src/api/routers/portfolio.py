"""Portfolio-wide statistics. Sprint 6 - Day 40"""
from fastapi import APIRouter
from src.api import db

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/stats")
def portfolio_stats() -> dict:
    """P10-P90 percentile table for 10 core KPIs across all companies."""
    return db.get_portfolio_stats()