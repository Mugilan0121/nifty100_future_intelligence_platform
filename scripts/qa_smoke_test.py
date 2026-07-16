"""
Day 27 — Integration QA & Bug Fixes

Smoke-tests the data-access layer (src/dashboard/utils/db.py) that all
8 Streamlit screens depend on. This doesn't click through the UI, but it
exercises every query path each page relies on, across:

  - 10 tickers spanning IT, Financials, FMCG, Energy, Healthcare
  - tickers with partial history (< 10 years of data)
  - screener-style extreme filtering (all metrics at min / max)
  - Company Profile load-time budget (< 3s per ticker)

Run from the project root:
    python scripts/qa_smoke_test.py
"""

import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "dashboard"))

import pandas as pd  # noqa: E402
from utils import db  # noqa: E402

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []  # (status, area, detail)


def log(status, area, detail=""):
    results.append((status, area, detail))
    print(f"[{status}] {area}" + (f" — {detail}" if detail else ""))


def safe_call(area, fn, *args, **kwargs):
    """Run fn, log FAIL on exception, return the result (or None)."""
    try:
        out = fn(*args, **kwargs)
        log(PASS, area)
        return out
    except Exception as e:
        log(FAIL, area, f"{type(e).__name__}: {e}")
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------
# 0. Base data
# ---------------------------------------------------------------------

print("\n=== Loading base tables ===")
companies = safe_call("get_companies()", db.get_companies)
sectors = safe_call("get_sectors()", db.get_sectors)
latest_ratios = safe_call("get_latest_ratios()", db.get_latest_ratios)
peer_groups = safe_call("get_peer_groups()", db.get_peer_groups)

if companies is None or companies.empty:
    print("\nCannot continue — get_companies() returned nothing. Check DB_PATH / loader.")
    sys.exit(1)

id_col = "id" if "id" in companies.columns else "company_id"

# ---------------------------------------------------------------------
# 1. Pick 10 tickers across target sectors (dynamic — no hardcoded tickers)
# ---------------------------------------------------------------------

TARGET_SECTORS_HINTS = ["IT", "Financial", "FMCG", "Energy", "Healthcare", "Pharma"]


def pick_tickers(n_per_sector=2, total=10):
    chosen = []
    if "broad_sector" not in companies.columns:
        return companies[id_col].dropna().unique().tolist()[:total]

    for hint in TARGET_SECTORS_HINTS:
        matches = companies[companies["broad_sector"].str.contains(hint, case=False, na=False)]
        for t in matches[id_col].dropna().unique().tolist():
            if t not in chosen:
                chosen.append(t)
            if len([c for c in chosen if c in matches[id_col].values]) >= n_per_sector:
                break
        if len(chosen) >= total:
            break

    # pad with anything else if target sectors under-supplied
    if len(chosen) < total:
        for t in companies[id_col].dropna().unique().tolist():
            if t not in chosen:
                chosen.append(t)
            if len(chosen) >= total:
                break

    return chosen[:total]


test_tickers = pick_tickers()
print(f"\n=== Testing {len(test_tickers)} tickers: {test_tickers} ===")

# ---------------------------------------------------------------------
# 2. Exercise every per-ticker query used across the 8 screens
# ---------------------------------------------------------------------

partial_data_tickers = []

for ticker in test_tickers:
    print(f"\n--- {ticker} ---")
    ratios = safe_call(f"get_ratios({ticker})", db.get_ratios, ticker)
    pl = safe_call(f"get_pl({ticker})", db.get_pl, ticker)
    bs = safe_call(f"get_bs({ticker})", db.get_bs, ticker)
    cf = safe_call(f"get_cf({ticker})", db.get_cf, ticker)
    pros_cons = safe_call(f"get_prosandcons({ticker})", db.get_prosandcons, ticker)
    docs = safe_call(f"get_documents({ticker})", db.get_documents, ticker)
    valuation = safe_call(f"get_valuation({ticker})", db.get_valuation, ticker)

    if pl is not None and len(pl) < 10:
        partial_data_tickers.append(ticker)
        log(WARN, f"partial data — {ticker}", f"only {len(pl)} years in profitandloss")

    # Check for NaN/None in key ratio columns that pages must render as N/A
    if ratios is not None and not ratios.empty:
        key_cols = [
            c for c in [
                "return_on_equity_pct", "return_on_capital_employed_pct",
                "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr",
                "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr",
                "pe_ratio", "pb_ratio", "ev_ebitda",
            ] if c in ratios.columns
        ]
        null_cols = [c for c in key_cols if ratios[c].isna().any()]
        if null_cols:
            log(WARN, f"nulls in ratios — {ticker}", f"columns with NaN: {null_cols}")

    # peer group membership for this ticker (used by Peer Comparison screen)
    if peer_groups is not None and not peer_groups.empty and "company_id" in peer_groups.columns:
        group_rows = peer_groups[peer_groups["company_id"] == ticker]
        for group_name in group_rows.get("peer_group_name", pd.Series(dtype=str)).unique():
            safe_call(f"get_peers({group_name}) via {ticker}", db.get_peers, group_name)
            safe_call(f"get_peer_percentiles({group_name}) via {ticker}", db.get_peer_percentiles, group_name)

    # is_url_valid — only test if documents exist, to avoid unnecessary network calls
    if docs is not None and not docs.empty:
        url_col = next((c for c in docs.columns if "url" in c.lower()), None)
        if url_col:
            sample_url = docs[url_col].dropna().astype(str).head(1).tolist()
            if sample_url:
                safe_call(f"is_url_valid({ticker})", db.is_url_valid, sample_url[0])

print(f"\n=== Partial-data tickers found: {partial_data_tickers or 'none'} ===")

# ---------------------------------------------------------------------
# 3. Screener — extreme slider values (min/max) should not crash
# ---------------------------------------------------------------------

print("\n=== Screener extreme-value test ===")
if latest_ratios is not None and not latest_ratios.empty:
    numeric_cols = latest_ratios.select_dtypes(include="number").columns.tolist()
    try:
        # simulate "all sliders at minimum" -> filter where every metric >= its min (should return all rows)
        min_filtered = latest_ratios.copy()
        for c in numeric_cols:
            lo = latest_ratios[c].min(skipna=True)
            min_filtered = min_filtered[min_filtered[c].fillna(lo) >= lo]
        log(PASS, "screener all-metrics-at-minimum", f"{len(min_filtered)} rows returned")

        # simulate "all sliders at maximum" -> filter where every metric <= its max (should return few/all rows)
        max_filtered = latest_ratios.copy()
        for c in numeric_cols:
            hi = latest_ratios[c].max(skipna=True)
            max_filtered = max_filtered[max_filtered[c].fillna(hi) <= hi]
        log(PASS, "screener all-metrics-at-maximum", f"{len(max_filtered)} rows returned")

        # simulate an impossible combo: min > actual max for one column (should return 0 rows, not crash)
        if numeric_cols:
            c = numeric_cols[0]
            impossible = latest_ratios[latest_ratios[c] > latest_ratios[c].max(skipna=True)]
            log(PASS, "screener impossible-range", f"{len(impossible)} rows returned (expect 0)")
    except Exception as e:
        log(FAIL, "screener extreme-value test", f"{type(e).__name__}: {e}")
        traceback.print_exc()
else:
    log(WARN, "screener extreme-value test", "latest_ratios empty/unavailable — skipped")

# ---------------------------------------------------------------------
# 4. Company Profile load-time budget — under 3s per ticker
# ---------------------------------------------------------------------

print("\n=== Company Profile timing test (5 tickers, target < 3.0s each) ===")
timing_tickers = test_tickers[:5]

for ticker in timing_tickers:
    start = time.perf_counter()
    try:
        db.get_ratios(ticker)
        db.get_pl(ticker)
        db.get_bs(ticker)
        db.get_cf(ticker)
        db.get_prosandcons(ticker)
        db.get_documents(ticker)
        elapsed = time.perf_counter() - start
        status = PASS if elapsed < 3.0 else FAIL
        log(status, f"profile load time — {ticker}", f"{elapsed:.2f}s")
    except Exception as e:
        log(FAIL, f"profile load time — {ticker}", f"{type(e).__name__}: {e}")
        traceback.print_exc()

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

print("\n" + "=" * 60)
n_pass = sum(1 for r in results if r[0] == PASS)
n_fail = sum(1 for r in results if r[0] == FAIL)
n_warn = sum(1 for r in results if r[0] == WARN)
print(f"SUMMARY: {n_pass} pass, {n_fail} fail, {n_warn} warnings")
print("=" * 60)

if n_fail:
    print("\nFAILURES:")
    for status, area, detail in results:
        if status == FAIL:
            print(f"  - {area}: {detail}")
    sys.exit(1)
else:
    print("\nAll smoke tests passed. Review warnings above for null/partial-data edge cases.")