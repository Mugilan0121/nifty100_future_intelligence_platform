"""Sector endpoints. Sprint 6 - Day 40"""
from fastapi import APIRouter, HTTPException
from src.api import db

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def list_sectors() -> dict:
    """All sectors with company_count, median_roe, median_pe, median_de."""
    sectors = db.get_sectors_list()
    return {"sector_count": len(sectors), "sectors": sectors}


@router.get("/sectors/{sector}/companies")
def sector_companies(sector: str) -> list[dict]:
    """Companies in a sector with latest-year KPIs."""
    if not db.sector_exists(sector):
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")
    return db.get_sector_companies(sector)