"""
Nifty 100 Future Intelligence Platform - FastAPI Server.

Sprint 6 - Day 38

Run with: uvicorn src.api.main:app --port 8000
Docs at:  http://localhost:8000/docs
"""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

app = FastAPI(
    title="Nifty 100 Future Intelligence Platform API",
    description="REST API for Nifty 100 equity screening, valuation, and sector analysis.",
    version="1.0.0",
)

# Internal-use dashboard only, all origins allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs method, path, and response time for every request."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    print(f"{request.method} {request.url.path} - {response.status_code} - {duration_ms}ms")
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")