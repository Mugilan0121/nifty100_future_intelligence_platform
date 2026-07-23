"""Peer group + radar comparison endpoints. Sprint 6 - Day 40"""
from fastapi import APIRouter, HTTPException
from src.api import db

router = APIRouter(tags=["peers"])


@router.get("/peers/{group_name}")
def peer_group(group_name: str) -> list[dict]:
    """Companies in a peer group with percentile rank per metric."""
    if not db.peer_group_exists(group_name):
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
    return db.get_peer_group_data(group_name)


@router.get("/companies/{ticker}/peers/compare")
def peer_radar(ticker: str) -> dict:
    """Radar data: company values + peer group avg + benchmark company."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    radar = db.get_peer_radar(ticker)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"No peer group assigned for '{ticker}'")
    return radar