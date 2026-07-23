"""Valuation endpoints. Sprint 6 - Day 40"""
from fastapi import APIRouter, HTTPException
from src.api import db

router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{ticker}")
def market_cap_history(ticker: str) -> dict:
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield), 2019-2024."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return {"ticker": ticker, "history": db.get_market_cap_history(ticker)}