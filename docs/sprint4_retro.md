# Sprint 4 Retrospective

## Sprint Goal

Build the Streamlit dashboard layer on top of the Sprint 3 analytics engine — 8 screens covering company profiles, screening, peer comparison, trend analysis, sector analysis, capital allocation, and annual reports — backed by a centralized cached data-access layer.

## What Went Well

- Built utils/db.py as a single cached data-access layer used by all 8 screens.
- Delivered all 8 Streamlit pages: Home, Company Profile, Screener, Peer Comparison, Trend Analysis, Sector  Analysis, Capital Allocation Map, Annual Reports.
- Persisted computed composite scores to SQLite via backfill_composite_score.py.
- Generated FCF yield and sector-relative P/E valuation flags via valuation.py.
- Built a reusable QA smoke-test script covering all 8 screens across 10 sector-diverse tickers.
- Full integration pass completed — zero crashes, all load times well under the 3-second budget.
- Fixed 5 bugs found during integration QA, including a silent join bug that was nulling valuation multiples for every company.


## Challenges Faced

- Silent bugs were the norm rather than the exception — nulls and broken joins failed quietly instead of throwing errors, requiring deliberate auditing rather than relying on visible crashes.
- A substr() join on a "Mon YYYY"-formatted year column was slicing the wrong end of the string, silently nulling PE, PB, and EV/EBITDA for every company and year.
- Company logos failed inconsistently — some rendered, some showed broken images — because server-side URL validation didn't reflect actual browser-side hotlink restrictions.
- Streamlit's hot-reload did not reliably pick up changes to shared utils/ modules, costing debugging time until a full server restart was used instead of a browser refresh.
- Styling a highlighted benchmark row required setting text color explicitly — background-only styling inherited illegible default text color.


## Improvements for Next Sprint

- Grep for other substr(year, ...) or similar string-slicing joins that may share the same off-by-direction bug.
- Run the QA smoke-test script before every sprint demo, not just once at integration time.
- Default to a full server restart (not browser refresh) whenever a fix to a shared utils/ module doesn't appear to take effect.
- Add automated null/NaN column checks to the smoke test as a standing regression guard, not just a one-time diagnostic.
- Consider validating image/logo URLs with actual <img> load behavior (client-side) rather than server-side HEAD/GET checks alone.


## Sprint Outcome

Sprint 4 completed successfully.

- All 8 dashboard screens load without errors across the full 92-company dataset.
- Company Profile screen loads in under 3 seconds (measured well under 0.1s).
- Screener extreme-value filtering and CSV export verified with no crashes.
- All identified bugs fixed and re-verified.
- Ready for Sprint 5.