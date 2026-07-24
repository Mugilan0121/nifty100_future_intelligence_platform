"""
Performance test: Company Profile screen load time on 5 tickers.

Sprint 6 - Day 43

Simulates the exact sequence of db.py calls that
src/dashboard/pages/02_profile.py makes for a given ticker, and times
each step separately so any bottleneck (e.g. the logo HTTP fetch) is
visible rather than hidden inside a single combined number.

Note: get_companies()/get_ratios()/etc. are decorated with
@st.cache_data, which works fine outside a running Streamlit session
(it just won't persist across script runs) — Streamlit may print a
"missing ScriptRunContext" warning to stderr, which is expected and
harmless for this standalone timing script.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "dashboard"))

from utils.db import get_companies, get_ratios, get_pl, get_prosandcons, get_logo_data_uri

TICKERS = ["TCS", "INFY", "ITC", "MARUTI", "LT"]


def time_step(label, func, *args):
    start = time.time()
    result = func(*args)
    elapsed = time.time() - start
    print(f"    {label:20s} {elapsed:6.3f}s")
    return result, elapsed


def profile_ticker(companies_df, ticker):
    print(f"\n--- {ticker} ---")
    total = 0.0

    ratios, t = time_step("get_ratios", get_ratios, ticker)
    total += t

    _, t = time_step("get_pl", get_pl, ticker)
    total += t

    _, t = time_step("get_prosandcons", get_prosandcons, ticker)
    total += t

    logo_url = None
    match = companies_df[companies_df["id"] == ticker]
    if not match.empty:
        logo_url = match.iloc[0].get("company_logo")

    if logo_url:
        _, t = time_step("get_logo_data_uri", get_logo_data_uri, logo_url)
        total += t
    else:
        print(f"    {'get_logo_data_uri':20s} skipped (no logo_url)")

    print(f"    {'TOTAL':20s} {total:6.3f}s  -> {'PASS' if total < 3 else 'FAIL'} (target: <3s)")
    return total


def main():
    print("=" * 50)
    print("Company Profile screen load time — 5 tickers")
    print("=" * 50)

    # get_companies() is loaded once and cached, same as the real page
    start = time.time()
    companies_df = get_companies()
    print(f"\nget_companies() (one-time, cached): {time.time() - start:.3f}s")

    results = {}
    for ticker in TICKERS:
        results[ticker] = profile_ticker(companies_df, ticker)

    print(f"\n{'='*50}")
    print("Summary")
    print(f"{'='*50}")
    for ticker, total in results.items():
        status = "PASS" if total < 3 else "FAIL"
        print(f"  {ticker:10s} {total:6.3f}s  {status}")

    all_pass = all(t < 3 for t in results.values())
    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILED'}")


if __name__ == "__main__":
    main()