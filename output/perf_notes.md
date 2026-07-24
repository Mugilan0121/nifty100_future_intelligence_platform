# Performance Test Notes — Sprint 6, Day 43

## 1. API Load Test — 10 concurrent screener requests

**Target:** all 10 requests complete within 10 seconds.
**Result: PASS** — before indexing: 3.192s total. After indexing: 3.341s total.

| Metric | Before indexes | After indexes |
|---|---|---|
| Total wall-clock time | 3.192s | 3.341s |
| Slowest individual request | 3.191s | 3.337s |

**Observation:** indexing made no meaningful difference (well within
run-to-run noise). This confirms the bottleneck is the *number* of
separate DB round-trips per request, not scan speed — at only 92 rows
per table, SQLite already performs fast full-table scans regardless
of indexes. `db.screen_companies()` calls `_latest_row()` twice per
company (against `financial_ratios` and `market_cap`), opening a new
connection each time — roughly 180+ round-trips per screener call.
Indexes were still added (see below) since they cost nothing and will
matter if the dataset grows well beyond 92 companies; the real fix for
today's scale would be batching these into 1–2 bulk queries per table
instead of per-company lookups — flagged as a follow-up, not done here.

## 2. Dashboard Company Profile Load Time — 5 tickers

**Target:** each ticker loads in under 3 seconds.
**Result: 3 of 5 PASS, 2 of 5 FAIL** (ITC, LT).

| Ticker | get_ratios | get_pl | get_prosandcons | get_logo_data_uri | Total | Status |
|---|---|---|---|---|---|---|
| TCS | 0.026s | 0.009s | 0.007s | 2.312s | 2.354s | PASS |
| INFY | 0.024s | 0.007s | 0.004s | 1.013s | 1.048s | PASS |
| ITC | 0.011s | 0.007s | 0.006s | 4.481s | 4.504s | **FAIL** |
| MARUTI | 0.009s | 0.007s | 0.010s | 1.542s | 1.567s | PASS |
| LT | 0.012s | 0.006s | 0.003s | 3.620s | 3.642s | **FAIL** |

**Root cause:** all SQLite-backed calls are consistently fast (under
30ms). The entire bottleneck is `get_logo_data_uri()`, a live outbound
HTTP fetch to download and base64-encode each company's logo — not a
database issue at all, so indexing has no effect here.

**Mitigating factor:** `get_logo_data_uri()` is `@st.cache_data(ttl=86400)`.
In real usage, the slow fetch happens once per logo per 24-hour window;
every subsequent view is served from cache in milliseconds. The numbers
above are worst-case cold-start timings.

**Recommendation (not implemented today):** pre-fetch and cache all 92
company logos to local disk during ETL, rather than fetching live per
session. Flagged for team lead review.

## 3. End-to-End Port Test

**Result: PASS.**

- FastAPI (port 8000) and Streamlit (port 8501) started simultaneously with no conflicts
- `GET /api/v1/health` → 200 OK, correct `db_row_counts`
- `GET http://localhost:8501` → 200 OK, valid app shell
- Manually confirmed Company Profile screen renders real data (tested with Adani Enterprises) — company card, all 6 KPI tiles, both charts, pros/cons section all populated correctly

## 4. SQLite Indexing

Added 16 indexes (`company_id` and/or `year`) across all core tables:
`financial_ratios`, `profitandloss`, `balancesheet`, `cashflow`,
`market_cap`, `sectors`, `documents`, `prosandcons`, `peer_groups`,
`peer_percentiles`, `stock_prices`. Zero indexes existed prior to this.
As noted in Section 1, no measurable performance change at current
data volume (92 companies) — indexes are a forward-looking investment
for when the dataset scales, not a fix for today's bottleneck.

## Summary

| Test | Result |
|---|---|
| API load test (10 concurrent) | PASS (3.2–3.3s / 10s target) |
| Dashboard profile load (5 tickers) | 3/5 PASS — bottleneck: live logo fetch, mitigated by 24h caching |
| End-to-end port test | PASS |
| SQLite indexing | Added, no measurable impact at current scale |