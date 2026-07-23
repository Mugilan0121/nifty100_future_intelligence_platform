"""Company document endpoints. Sprint 6 - Day 40"""
from fastapi import APIRouter, HTTPException
from src.api import db

router = APIRouter(tags=["documents"])


@router.get("/companies/{ticker}/documents")
def company_documents(ticker: str) -> list[dict]:
    """Annual report links with is_url_valid flag for each."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return db.get_company_documents(ticker)