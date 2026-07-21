"""
Company data endpoints.

Sprint 6 - Day 39
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api import db

router = APIRouter(tags=["companies"])


@router.get("/companies")
def list_companies(
    sector: str | None = Query(default=None, description="Filter by broad_sector"),
    market_cap_category: str | None = Query(default=None),
    search: str | None = Query(default=None, description="Partial company name or ticker match"),
) -> list[dict]:
    """All 92 companies, filterable by sector, market_cap_category, and search."""
    return db.get_companies_list(sector=sector, market_cap_category=market_cap_category, search=search)


@router.get("/companies/{ticker}")
def get_company(ticker: str) -> dict:
    """Full company profile: companies fields + sector data + latest year's ratios."""
    ticker = db.normalize_ticker(ticker)
    profile = db.get_company_profile(ticker)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return profile


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
    to_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
) -> list[dict]:
    """P&L history for a company, optionally filtered to a year range."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return db.get_statement("profitandloss", ticker, from_year, to_year)


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
    to_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
) -> list[dict]:
    """Balance sheet history for a company, optionally filtered to a year range."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return db.get_statement("balancesheet", ticker, from_year, to_year)


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
    to_year: str | None = Query(default=None, description="YYYY-MM, inclusive"),
) -> list[dict]:
    """Cash flow history for a company, optionally filtered to a year range."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return db.get_statement("cashflow", ticker, from_year, to_year)


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: str | None = Query(default=None, description="Any recognizable year format; returns a single matching year"),
) -> list[dict]:
    """All computed KPIs per year for a company, or a single year if given."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
    return db.get_company_ratios(ticker, year=year)


@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str) -> FileResponse:
    """Pre-generated tearsheet PDF as a binary file download."""
    ticker = db.normalize_ticker(ticker)
    with db.get_connection() as conn:
        if not db.company_exists(conn, ticker):
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    path = db.get_tearsheet_path(ticker)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Tearsheet not found for '{ticker}'")

    return FileResponse(path, media_type="application/pdf", filename=path.name)