"""Screener endpoint. Sprint 6 - Day 40"""
from fastapi import APIRouter, HTTPException, Query
from src.api import db

router = APIRouter(tags=["screener"])


@router.get("/screener")
def screener(
    min_roe: float | None = Query(default=None),
    max_de: float | None = Query(default=None),
    min_fcf: float | None = Query(default=None),
    sector: str | None = Query(default=None),
    min_rev_cagr_5yr: float | None = Query(default=None),
    min_pat_cagr_5yr: float | None = Query(default=None),
    max_pe: float | None = Query(default=None),
) -> dict:
    """Ranked company list filtered by screener criteria."""
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative")
    if min_roe is not None and (min_roe < -500 or min_roe > 500):
        raise HTTPException(status_code=400, detail="min_roe out of plausible range")

    results = db.screen_companies(
        min_roe=min_roe, max_de=max_de, min_fcf=min_fcf, sector=sector,
        min_rev_cagr_5yr=min_rev_cagr_5yr, min_pat_cagr_5yr=min_pat_cagr_5yr, max_pe=max_pe,
    )
    return {"count": len(results), "results": results}