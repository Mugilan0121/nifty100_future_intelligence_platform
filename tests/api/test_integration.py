"""
Integration test: dashboard screener results vs. API screener endpoint.

Sprint 6 - Day 42

Only min_roe is compared directly, since it's the one filter both
paths implement identically (latest-year return_on_equity_pct >=
threshold, no sector carve-outs, no cross-table year-matching).

Known discrepancies NOT covered by this test (flagged for review,
not silently reconciled):
- Dashboard's D/E filter excludes Financials-sector companies
  (src/dashboard/pages/03_screener.py); the API's screen_companies()
  applies max_de uniformly with no sector exception.
- Dashboard exposes an ICR (interest coverage) filter; the API
  screener has no icr_min parameter at all.
- Dashboard joins financial_ratios to market_cap by matching year
  exactly; the API takes the latest row from each table independently,
  which can diverge if a company's latest ratio year and latest
  market_cap year differ.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "dashboard"))

from utils.db import get_latest_ratios


def test_min_roe_filter_matches_between_dashboard_and_api(client):
    threshold = 15

    # Dashboard-side: same logic as 03_screener.py's ROE filter
    dashboard_df = get_latest_ratios()
    dashboard_ids = set(
        dashboard_df[dashboard_df["return_on_equity_pct"] >= threshold]["company_id"]
    )

    # API-side
    response = client.get(f"/api/v1/screener?min_roe={threshold}")
    assert response.status_code == 200
    api_ids = {row["id"] for row in response.json()["results"]}

    assert dashboard_ids == api_ids, (
        f"Dashboard and API disagree on ROE>={threshold} results. "
        f"Only in dashboard: {dashboard_ids - api_ids}. "
        f"Only in API: {api_ids - dashboard_ids}."
    )