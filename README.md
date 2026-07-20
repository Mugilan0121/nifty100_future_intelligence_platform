# Nifty 100 Financial Intelligence Platform

Financial Intelligence Platform for 92 Nifty 100 companies.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

```

## Sprint 1 Progress

### Day 1 – Environment Setup
Completed project setup, virtual environment configuration, dependency installation, and environment variable configuration.

### Day 2 – Excel Loader & Normaliser
Implemented Excel loading functionality for core datasets, developed data normalisation utilities, and completed 40 passing unit tests.

### Day 3 - Schema Validator-- 16DQ Rules
Implemented Data Quality Validation Framework with 16 validation rules covering primary keys, foreign keys, financial consistency checks, format validation, ratio validation, URL checks, and dataset coverage checks. Validation failures are logged and exported to CSV for auditing.

### Day 4 - SQL Database Schema
Implemented SQLite database schema with primary and foreign key relationships. Developed database loading pipeline to ingest all project datasets and validated successful data loading through table, relationship, and row count checks.

### Day 5 – Full Data Load

- Loaded all 12 datasets (7 core + 5 supplementary) into SQLite.
- Verified load order and populated all database tables.
- Generated load_audit.csv with per-table row counts and rejection metrics.
- Confirmed expected row counts:
  - Companies: 92
  - Profit & Loss: 1276
  - Balance Sheet: 1312
  - Cash Flow: 1187
  - Stock Prices: 5520
- Performed foreign key validation with 0 violations.
- Successfully created and validated nifty100.db.

### Day 6 - Data Quality Manual Review

Performed manual data quality review on 5 randomly selected companies ( HEROMOTOCO, TATAMOTORS, NHPC, ATGL, and TRENT). Verified historical data coverage across Profit & Loss , Balance Sheet, and Cash Flow tables. Investigated data completeness and validated DQ-16 checks for companies with less than 5 years of history. Identified JIOFIN as a valid business exception with 3 years of available data. Confirmed no ETL loader defects or schema issues requiring remediation.

### Day 7 - Sprint 1 Wrap-Up & Review

Created and validated `exploratory_queries.sql` with 10 exploratory SQL queries covering row counts, data coverage, and integrity checks. Successfully executed all queries against `nifty100.db` and verified database functionality. Completed Sprint 1 review by validating database outputs, confirming 92 companies loaded, verifying foreign key integrity, and running the ETL test suite with 40 passing tests and 0 failures. Documented Sprint 1 retrospective and confirmed all Sprint 1 deliverables and exit criteria were successfully achieved.

## Sprint 2 Progress

### Day 8 - Financial Ratio Engine (Profitability Ratios)

Started Sprint 2 by developing the Financial Ratio Engine for profitability analysis. Created `src/analytics/ratios.py` and implemented Net Profit Margin (NPM), Operating Profit Margin (OPM), Return on Equity (ROE), and Return on Capital Employed (ROCE) with proper edge case handling for zero sales, negative equity, and invalid capital employed values. Added OPM source cross-check logic with anomaly logging for mismatches greater than 1%.

Created `tests/kpi/test_ratios.py` and developed 8 unit tests covering normal calculations and edge cases for all implemented profitability ratios. Successfully executed the complete test suite with **8/8 tests passing** and **0 failures**, confirming the correctness of the implemented KPI calculations and laying the foundation for the remaining financial ratio engine in Sprint 2.

### Day 09 – Leverage & Efficiency Ratios

- Implemented Debt-to-Equity (D/E) ratio with debt-free handling.
- Added High Leverage Flag for non-financial companies.
- Implemented Interest Coverage Ratio (ICR) with debt-free support.
- Added Debt Free display label and ICR warning flag.
- Implemented Net Debt calculation.
- Implemented Asset Turnover ratio.
- Added 8 unit tests covering leverage and efficiency ratios.
- Successfully passed all 16 KPI unit tests (Day 8 + Day 9).

### Day 10 - CAGR Engine

- Implemented reusable CAGR calculation engine in `src/analytics/cagr.py`.
- Added Revenue CAGR, PAT CAGR, and EPS CAGR wrapper functions.
- Implemented all required CAGR edge-case handlers:
  - DECLINE_TO_LOSS
  - TURNAROUND
  - BOTH_NEGATIVE
  - ZERO_BASE
  - INSUFFICIENT
- Added 10 pytest unit tests covering normal calculations, edge cases, and wrapper functions.
- Verified all tests passed successfully.

### Day 11 – Cash Flow KPIs & Capital Allocation

- Implemented Free Cash Flow (FCF) calculation.
- Added CFO Quality Score with quality classification.
- Implemented CapEx Intensity calculation and classification.
- Added FCF Conversion Rate with efficiency classification.
- Built an 8-pattern Capital Allocation classifier using operating, investing and financing cash flow signs.
- Generated `output/capital_allocation.csv` with capital allocation patterns for every company-year.
- Developed 35 unit tests covering KPI calculations, classifications and capital allocation scenarios.

### Day 12 - Financial Ratios Population

- Developed the financial ratio population engine.
- Merged Companies, Profit & Loss, Balance Sheet, and Cash Flow tables.
- Calculated key financial KPIs for every company across all available years.
- Implemented 5-year Revenue, PAT, and EPS CAGR calculations.
- Added Composite Quality Score for overall financial health assessment.
- Populated the `financial_ratios` table in SQLite.
- Verified successful insertion of 1,184 records.
- Performed manual validation of ROE and Revenue CAGR for selected companies.
- Added unit tests to validate financial ratio calculations and data population.

### Day 13 - Bank ROCE Carve-Out & Edge Case Logging

- Added Return on Capital Employed (ROCE) calculation to the financial ratio engine.
- Implemented ROE and ROCE validation against reference values from the `companies` table.
- Developed a dedicated `ratio_edge_cases.py` validation module.
- Generated `ratio_edge_cases.log` to capture ROE and ROCE anomalies.
- Categorized ratio validation anomalies for easier analysis and review.
- Separated ratio validation from financial ratio population for a cleaner project structure.
- Verified successful generation of the edge case log and validation workflow.

### Day 14 - Testing & Sprint 2 Wrap-up

- Executed all KPI unit tests (64/64 passed).
- Validated financial ratio calculations and database outputs.
- Reviewed `ratio_edge_cases.log` for ROE/ROCE validation.
- Verified `financial_ratios` SQLite table (1,184 records).
- Performed SQL screening queries for high-quality companies.
- Completed Sprint 2 review, documentation, and retrospective.

## Sprint 3 Progress

### Day 15 - Filter Engine Core

- Developed the financial screener engine in `src/screener/engine.py`.
- Implemented configuration loading from `config/screener_config.yaml`.
- Loaded financial ratios from SQLite with sector information using SQL joins.
- Built a generic threshold-based filtering engine supporting configurable metrics.
- Added Debt-to-Equity filtering while automatically excluding Financial sector companies.
- Implemented Interest Coverage filtering where Debt-Free companies automatically pass the filter.
- Sorted screening results by `composite_quality_score` in descending order.
- Validated the filter engine with function-level tests for data loading, generic filtering, D/E filtering, and ICR filtering.

### Day 16 - Preset Screeners

- Implemented six preset screeners in `config/screener_config.yaml`:
  Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion,
  Debt-Free Blue Chip, and Turnaround Watch.
- Extended `src/screener/engine.py` to load additional metrics from
  `market_cap`, `profitandloss`, and `sectors` using SQL joins.
- Filtered only the latest annual financial records and removed duplicate
  company-year entries before screening.
- Applied preset-specific threshold filters along with special handling for
  Debt-to-Equity (excluding Financial sector companies) and Interest Coverage
  (Debt-Free companies automatically pass).
- Validated all six presets on the 92-company universe and confirmed each
  returns between 5 and 50 companies as required.
- Ranked screening results using `composite_quality_score` and verified the
  output for each preset.

  ### Day 17 - Composite Score & Screener Export

- Implemented a weighted `composite_quality_score` (0–100) using
  Profitability, Cash Quality, Growth, and Leverage metrics.
- Added P10/P90 winsorization and normalized all scoring metrics
  before calculating the final composite score.
- Calculated `sector_relative_score` by normalizing composite scores
  within each `broad_sector` for peer-based comparison.
- Extended `src/screener/engine.py` to export
  `output/screener_output.xlsx` with six preset worksheets sorted by
  `composite_quality_score` in descending order.
- Applied Excel conditional formatting to highlight preset threshold
  results using green (pass) and red (fail) cell colours.
- Verified all six screener exports and confirmed correct composite
  scoring, sector-relative scoring, sorting, and colour-coded output.

  ### Day 18 - Peer Percentile Rankings

- Developed the `peer.py` analytics module to compute peer percentile rankings.
- Loaded peer group mappings from `peer_groups.xlsx` and merged them with financial ratio data.
- Calculated percentile rankings for 10 financial metrics across all 11 peer groups.
- Applied inverse percentile ranking for Debt-to-Equity so lower values receive higher rankings.
- Added handling for companies without a peer group assignment without interrupting execution.
- Created and populated the `peer_percentiles` SQLite table with company-wise percentile rankings.
- Verified successful generation and storage of 7,300 peer percentile records.

### Day 19 - Radar Chart Generation

- Developed the `radar.py` analytics module to generate radar charts for the latest financial data.
- Merged financial ratios with peer group mappings to prepare comparison datasets.
- Calculated peer-group averages and used Nifty100 averages as fallback reference values.
- Implemented radar/polar charts with eight financial metrics including ROE, ROCE, NPM, D/E, FCF, PAT CAGR, Revenue CAGR, and Composite Quality Score.
- Applied metric normalization to improve readability across different financial scales.
- Exported one PNG radar chart per company to `reports/radar_charts/`.
- Verified successful generation of radar chart images for all available companies.

### Day 20 - Peer Comparison Excel Report

- Developed Excel report generation for peer-wise financial comparison across all 11 peer groups.
- Generated `output/peer_comparison.xlsx` with one worksheet for each peer group.
- Included company details, financial metrics, and percentile rankings for comparison.
- Applied conditional formatting to percentile columns using green (>=75th), yellow (25th–75th), and red (<=25th) colour coding.
- Highlighted the benchmark company row with an amber background for quick identification.
- Added a peer median summary row at the bottom of every worksheet.
- Verified successful export and formatting of the complete peer comparison workbook.

### Day 21 - Testing, Validation & Sprint 3 Review

- Executed the complete project test suite to validate Sprint 3 functionality.
- Successfully passed all 104 automated unit tests with zero failures.
- Verified the Quality Compounder screener preset by manually validating the top five screened companies against the configured ROE and Debt-to-Equity thresholds.
- Performed manual verification of peer comparison reports for the IT Services and FMCG peer groups to ensure ranking consistency.
- Confirmed successful generation of all Sprint 3 deliverables, including screener reports, peer comparison workbook, radar charts, peer percentile data, and configuration files.
- Created Sprint 3 Summary and Sprint 3 Retrospective documentation.
- Completed Sprint 3 quality assurance, testing, and review, confirming the project is ready to proceed to Sprint 4.

## Sprint 4 Progress

### Day 22 - Streamlit App Scaffold

- Created `src/dashboard/app.py` as the main Streamlit entry point with sidebar navigation to all 8 screens.
- Built `src/dashboard/utils/db.py` as a shared, cached data-access layer — every screen reads through this module instead of querying SQLite directly.
- Implemented core data loaders: `get_companies()`, `get_ratios()`, `get_latest_ratios()`, `get_pl()`, `get_bs()`, `get_cf()`, `get_peers()`, `get_capital_allocation()`, and `get_valuation()`, all wrapped in `@st.cache_data(ttl=600)`.
- Set Streamlit page config: wide layout, page title "Nifty 100 Analytics," sidebar expanded by default.
- Verified `streamlit run src/dashboard/app.py` launches cleanly with no import errors.

### Day 23 - Home Screen & Company Profile Screen

- Home screen (`pages/01_home.py`): 6 summary KPI tiles (Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR 5yr, Debt-Free Companies count), sector breakdown donut chart, and a Top-5-by-Composite-Quality-Score table.
- Added a year selector in the sidebar; all Home metrics update on year change.
- Company Profile screen (`pages/02_profile.py`): dropdown-based company search with autocomplete, company card (name, sector, description), 6 KPI tiles (ROE, ROCE, Net Profit Margin, D/E, Revenue CAGR 5yr, FCF), a 10-year Revenue vs Net Profit bar chart, a ROE vs ROCE dual-line trend chart, and a pros/cons section.
- Discovered and fixed a bug in `src/screener/engine.py`: the final two lines (`export_screener_output` call and print statement) were not indented under `if __name__ == "__main__":`, causing them to execute on every import and break any script importing the module.
- Created `src/analytics/backfill_composite_score.py` to persist `composite_quality_score` and `sector_relative_score` into the `financial_ratios` table, since these were previously computed only at runtime inside the screener and weren't available to other screens.

### Day 24 - Screener Screen & Peer Comparison Screen

- Screener screen (`pages/03_screener.py`): 10 sidebar sliders (ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, Interest Coverage), 6 preset buttons that auto-fill thresholds, a live-updating results table, a company-count label, and a CSV download button.
- Replicated the Debt-to-Equity (exclude Financials) and Interest Coverage (debt-free auto-pass) business rules from the Sprint 3 screener engine directly in the dashboard filter logic.
- Peer Comparison screen (`pages/04_peers.py`): peer group dropdown covering all 11 groups, a normalized 8-axis radar chart (company vs. group average vs. benchmark), and a side-by-side comparison table with the benchmark row highlighted.
- Fixed a data-join bug in `utils/db.py`: the `market_cap` join used `substr(fr.year, -4)` instead of `substr(fr.year, 1, 4)`, which silently returned null valuation columns (P/E, P/B, dividend yield) across the Home and Screener screens.

### Day 25 - Remaining 4 Screens

- Trend Analysis (`pages/05_trends.py`): company search, multi-metric selector (overlay up to 3 metrics), 10-year trend chart with hover-based YoY change tooltips, and a secondary y-axis for ratio-scale metrics (D/E, Asset Turnover) so they don't flatten against percentage-scale metrics (ROE, ROCE).
- Sector Analysis (`pages/06_sectors.py`): sector dropdown, a Revenue vs. ROE bubble chart (bubble size = market cap, color = sub-sector), and a sector median KPI bar chart. Added a fallback bubble size and a missing-data caveat for sectors where market cap coverage is incomplete for the latest year.
- Capital Allocation Map (`pages/07_capital.py`): treemap of all companies by capital allocation pattern, with a dropdown-driven drill-down table. Corrected the year-handling logic to use each company's most recent available year individually, since fiscal year-ends vary by company (Mar/Jun/Sep/Dec) and no single shared calendar year exists across the universe.
- Annual Reports (`pages/08_reports.py`): company search, year filter, and clickable BSE PDF links. Added a cached, browser-header-spoofed `is_url_valid()` check in `utils/db.py` to flag genuinely broken links with a red "Report unavailable" badge, mirroring the project's DQ-13 validation rule.
- Added `LEFT JOIN profitandloss` to the `get_ratios()` query in `utils/db.py` after discovering `sales` and `net_profit` were missing from the financial ratios data layer, which had been silently blocking the Sector Analysis bubble chart.

### Day 26 - Valuation Module

- Built `src/analytics/valuation.py`, reading `market_cap` history joined with company, sector, and latest free cash flow data.
- Computed FCF Yield (`FCF / Market Cap × 100`), 5-year median P/E per company, and sector median P/E based on each company's latest year.
- Implemented the overvaluation flag rule: P/E > sector median × 1.5 → "Caution"; P/E < sector median × 0.7 → "Discount"; otherwise "Fair."
- Generated `output/valuation_summary.xlsx` (all companies, latest-year valuation metrics and flags) and `output/valuation_flags.csv` (Caution/Discount companies only, sorted by deviation from sector median).
- Identified a data-quality issue during review: `NHPC`'s `company_name` field contains an embedded newline character (`"NHPC Ltd\n"`), consistent with the known data quirk documented in the project's dataset catalogue — flagged for a future ETL cleanup pass rather than fixed inline in the dashboard.

### Day 27 - Integration QA & Bug Fixes

- Built scripts/qa_smoke_test.py, a reusable smoke test that dynamically pulls 10 tickers spanning IT, Financials, FMCG, Energy, and Healthcare from get_companies() and exercises every query path used across all 8 screens — get_ratios, get_pl, get_bs, get_cf, get_prosandcons, get_documents, get_valuation, get_peers, get_peer_percentiles — logging PASS/FAIL/WARN per call rather than relying on manual click-through.
- Confirmed no crashes across all 92 companies; flagged ADANIGREEN as a genuine partial-data case (9 years of P&L history vs. the usual 10) rather than a loader bug.
- Found and fixed a silent join bug in get_ratios(): the join to market_cap used substr(fr.year, 1, 4) on values like "Mar 2013", which returns "Mar " instead of the year — silently nulling pe_ratio, pb_ratio, and ev_ebitda for every company across every year. Changed to substr(fr.year, -4) to correctly extract the year digits.
- Fixed a text-contrast bug on the Peer Comparison benchmark row (pages/04_peers.py) where the highlight style set background-color without color, making the row illegible; added explicit color: #000000.
- Fixed a NameError in pages/04_peers.py from a leftover df_display reference to a variable renamed during refactor; removed the dead line and standardized on table_df.
- Diagnosed inconsistent company-logo rendering on the Company Profile screen: server-side is_url_valid() checks passed but some logos still failed to render client-side due to hotlink protection the requests library doesn't trigger. Replaced the approach with get_logo_data_uri() in utils/db.py — downloads the logo server-side with browser-mimicking headers and embeds it as a cached base64 data URI, falling back to a placeholder tile only when the source is genuinely unreachable.
- Simulated Screener slider-extreme behavior (all-minimum, all-maximum, and an impossible range) directly against get_latest_ratios() — confirmed no crash and correct empty-result handling.
- Measured Company Profile full query-set load time (ratios + P&L + BS + CF + pros/cons + documents) across 5 tickers — all completed in under 0.1s, well inside the 3-second budget.

### Day 28 - Retro, Documentation and Sprint 4 wrap-up

- Updated README.md with Day 27–28 entries documenting the QA pass, root causes, and fixes.
- Wrote docs/sprint4_retro.md following the project's established retro format (Sprint Goal / What Went Well / Challenges Faced / Improvements for Next Sprint / Sprint Outcome), covering the dashboard build, the 5 bugs found and fixed, and process notes — most notably that Streamlit's hot-reload doesn't reliably pick up changes to shared utils/ modules, requiring a full server restart rather than a browser refresh.
- Wrote docs/sprint4_summary.md with a condensed overview of what was built, fixed, and verified.
- Confirmed exit criteria: all 8 screens load without errors across all 92 tickers, Company Profile loads well under 3 seconds, Screener CSV export produces correct headers under extreme filter values, and valuation_summary.xlsx contains 92 rows with all required columns.

## Sprint 5 Progress

### Day 29 - NLP Analysis Text Parser

- Discovered the analysis table structure differs from the initial spec assumption: rather than one row per company with multi-period text packed into each cell, it stores one row per (company, period) — e.g. HDFCBANK has a single 10-year row, while SBILIFE has separate 5-year and 3-year rows, with all 4 metric columns in a row sharing that row's period label.
- Built src/nlp/parser.py, parsing compounded_sales_growth, compounded_profit_growth, stock_price_cagr, and roe using the regex pattern (\d+)\s*Years?:?\s*(-?[\d.]+)\s*%, with the colon made optional to handle inconsistently formatted entries like "5 Years 14%".
- Found the initial pattern was silently dropping negative values ("1 Year: -2%", "3 Years: -1%") because [\d.]+ didn't permit a minus sign; added -? to capture negative CAGR and stock-return figures correctly.
- Generated output/analysis_parsed.csv with 65 parsed rows in long format (company_id, metric_type, period_years, value_pct).
- Generated output/parse_failures.csv with 15 rows — all genuinely outside the "N Years:" format (e.g. "TTM: 43%", "Last Year: 12%"), logged for the ETL cleanup catalogue rather than force-matched.
- Cross-validated 5-year parsed compounded_sales_growth and compounded_profit_growth against computed revenue_cagr_5yr and pat_cagr_5yr from financial_ratios, flagging divergence greater than 5 percentage points into output/cagr_divergence.csv — 0 companies flagged, confirming the parsed and computed CAGR figures agree.


### Day 30 - NLP Auto Pros/Cons Generator

- Built src/nlp/pros_cons_generator.py implementing all 12 pro rules and 12 con rules against financial_ratios, balancesheet, and profitandloss, with a documented confidence heuristic and only rules above 60% confidence included in the output.
- Resolved a spec conflict in Pro Rule 11 (header vs. rule text implied opposite conditions) by implementing per the text — genuine operating leverage (PAT CAGR > Revenue CAGR).
- Approximated Con Rule 11's "Net Debt" as gross total_debt_cr, since balancesheet has no cash balance column to net against.
- Fixed a crash from a malformed year value ("24.5") by making year-parsing fail gracefully and log/exclude bad rows instead of erroring out.
- Identified 103 non-annual "TTM"/stub-period rows in profitandloss and 5 malformed years in balancesheet — correctly excluded from trend rules rather than misread as fiscal years.
- Found 38 companies initially failed the "at least 1 pro and 1 con" requirement due to strict thresholds; added documented fallback rules (clearly labeled, lower confidence) that report the most relevant available metric instead of leaving a side empty.
- Found 2 companies (ATGL, SBIN) with zero financial_ratios history; added a last-resort fallback using roe_percentage/roce_percentage from the companies table.
- Verified output/pros_cons_generated.csv (551 rows, 92 companies) with the coverage check passing — every company has at least 1 pro and 1 con.

### Day 31 - Cash Flow Intelligence Module

- Found src/analytics/cashflow_kpis.py already existed from Sprint 2 with FCF, CFO Quality, CapEx Intensity, and the 8-pattern capital allocation classifier — extended it with fcf_cagr(), distress_signal(), and deleveraging_flag() rather than rebuilding.
- Implemented Distress Signal as its own check (CFO<0 AND CFF>0), since it's broader than the existing classifier's DISTRESS label, which also requires CFI<0.
- Built src/analytics/generate_cashflow_intelligence.py, reconciling the cashflow table's "Mar-13" year format against the "Mar 2013" format used elsewhere.
- Included ATGL (zero cashflow rows, consistent with Day 30's finding) with null metrics instead of dropping it, to meet the 92-row exit criterion.
- Generated output/cashflow_intelligence.xlsx (92 rows) and output/distress_alerts.csv (13 companies flagged).
- Flagged capital_allocation.csv's 100-vs-92 company count discrepancy for investigation on Day 32.

### Day 32 - Capital Allocation Report

- Investigated the 100-vs-92 company discrepancy flagged on Day 31 and found two separate causes: a ticker typo (AGTL should be ATGL) and 8 companies that have financial data but were never in the companies metadata source at all — confirmed via the raw source file, not a loader bug.
- Fixed the AGTL→ATGL typo; documented the 8 missing companies as a Sprint 1 scope mismatch rather than retroactively expanding the universe mid-sprint.
- Verified capital_allocation.csv now covers all 92 known companies with 0 missing.
- Generated output/capital_allocation_distribution.csv — latest-year pattern counts (REINVESTOR 56, GROWTH_FINANCING 13, DISTRESS 12, SHAREHOLDER_RETURNS 7, ASSET_LIQUIDATION 2, CASH_BURN 1, EXTERNAL_FUNDING 1).
- Confirmed cashflow_intelligence.xlsx already has the capital_allocation_label column from Day 31 — no rework needed.
- Generated output/pattern_changes.csv — 431 year-over-year pattern-change events.

### Day 33 - PDF Tearsheet Template

- Built src/reports/tearsheet.py implementing the 2-page company tearsheet using ReportLab: Page 1 — navy header bar with company name/ticker, 6 KPI tiles (ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF) in 2 rows of 3, a 10-year Revenue vs Net Profit bar chart, and a ROE vs ROCE line chart. Page 2 — Balance Sheet composition stacked bar (equity, borrowings, other liabilities), a Cash Flow waterfall for the latest year, a Pros/Cons table, and a color-coded Capital Allocation badge.
- Used matplotlib to render each chart to a PNG buffer and embedded them as ReportLab Image flowables, since ReportLab has no native charting.
- Satisfied the WORDWRAP requirement by wrapping all table cell content in Paragraph flowables instead of raw strings, so long company names or pros/cons text wrap within their cell rather than overflowing.
- Reused the flexible year parser from Days 30-32 to normalize the cashflow table's differing year format for the cash flow waterfall.
- Pulled pros/cons directly from output/pros_cons_generated.csv (sorted by confidence) and the capital allocation label from output/cashflow_intelligence.xlsx, reusing both Sprint 5 outputs rather than recomputing them.
- Tested on the 5 spec-named companies across different sectors (TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL) — all 5 PDFs generated successfully (112-125 KB each), visually confirmed correct with no text overflow or layout issues.

### Day 34 - Batch Report Generation

- Built src/reports/generate_all_tearsheets.py (batch runner for all 92 companies, reusing Day 33's build_tearsheet()) and src/reports/sector_report.py (10 sector PDFs with median KPI tiles + 8-metric company tables).
- Confirmed the dataset genuinely has 10 sectors, not the 11 the sprint plan mentioned — not a bug, just an inaccurate plan figure.
- Caught a serious pre-existing data bug while spot-checking reports: financial_ratios ROE/ROCE values are corrupted for BEL and HAL (thousands of percent instead of ~26-29%), traced to Sprint 2's ratio engine — flagged for the team lead rather than patched retroactively, since it likely also skewed Day 30's pros/cons and earlier screener outputs for these two companies.
- Added a display-layer sanity guard (values beyond ±200% shown as N/A*, excluded from medians/charts) in both report scripts, and fixed a follow-up TypeError on PNB from a None-vs-NaN dtype issue in that guard.
- Final result: 89/92 tearsheets generated (3 expected skips — ATGL, JIOFIN, SBIN), all ≥30 KB, and all 10 sector PDFs generated successfully.

shorter version

## Day 35 - Portfolio Summary PDF & Sprint 5 Wrap-Up

- Built src/reports/portfolio_summary.py — one page per company (alphabetical by ticker) with 6 KPI tiles and trend arrows vs. the prior year, reusing formatting functions from tearsheet.py so the Day 34 ROE/ROCE sanity guard carries over automatically.
- Documented two judgment calls the spec left unspecified: D/E is inverted (a decrease is "improved"), and "flat within 2%" is interpreted per-metric (percentage points for %-scale metrics, relative change for FCF).
- Generated reports/portfolio/portfolio_summary.pdf — 90 company pages. ATGL/SBIN skipped (no financial data); JIOFIN included here despite being skipped from tearsheets, since this report only needs 1+ year of data vs. tearsheets' 3-year minimum.
- Wrote docs/sprint5_retro.md and docs/sprint5_summary.md covering the full Day 29-35 arc.
- Confirmed all Sprint 5 exit criteria met, and flagged the BEL/HAL financial_ratios data bug (found Day 34) for team lead review ahead of sign-off.

## Sprint 6 Progress

### Day 36 - KMeans Clustering

- Built src/analytics/clustering.py, clustering all companies into 5 archetypes using return_on_equity_pct, debt_to_equity, revenue_cagr_5yr, fcf_cagr_5yr, and operating_profit_margin_pct, with sector-median imputation for missing values, StandardScaler normalization, and KMeans (k=5, random_state=42).
- Reused fcf_cagr_5yr from Day 31's output/cashflow_intelligence.xlsx rather than recomputing it, since financial_ratios has no such column.
- Found the companies table and financial_ratios table define slightly different 92-company universes: ULTRACEMCO and UNIONBANK exist in financial_ratios but not in companies, while ATGL and SBIN are the reverse (zero financial_ratios rows, known since Day 30). Restricted clustering to the companies table as the canonical 92 (matches Gate AC-01) and excluded the former pair rather than expanding the universe mid-sprint, per the Day 32 precedent.
- Added ATGL and SBIN back into cluster_labels.csv with a "No Data" cluster label rather than dropping them, so all 92 companies appear in the output and Gate AC-15 is satisfied.
- Generated reports/elbow_plot.png (inertia for k=2 to 10) - the bend around k=5 is present but not razor-sharp, typical for real financial data.
- Generated output/cluster_labels.csv (92 rows: company_id, cluster_id, cluster_name, distance_from_centroid).

### Day 37 - Cluster Profiling & Statistics

- Discovered the initial clustering was badly distorted by the Day 34 BEL/HAL corrupted-ROE bug (thousands of percent instead of ~26-29%): left uncorrected, the two outliers wrecked StandardScaler's mean/std for the ROE feature and collapsed every other company's scaled ROE toward zero, producing one lopsided 58-company mega-cluster. Applied the same +-200% sanity guard already used in tearsheet.py and sector_report.py before imputation, which fixed the distribution.
- Profiled all 5 clusters by mean/median of the 5 input features and by inspecting actual company membership. Two of the sprint doc's example names ("Value Cyclicals", "Emerging Growth") didn't match any cluster's real composition, so they were swapped for names that do: Core Compounders, Defensive Dividend Payers, Leveraged Financials, Distressed or Turnaround, High-Quality Compounders.
- Found KMeans's cluster_id numbering isn't guaranteed identical across scikit-learn versions/machines even with the same random_state - the same code produced a different id-to-group mapping on a different machine. Replaced the static {cluster_id: name} lookup with assign_cluster_names(), which derives each cluster's name from its own computed profile (highest FCF CAGR -> turnaround, highest D/E -> leveraged financials, highest ROE -> high-quality, highest OPM -> defensive, remainder -> core), so naming is correct regardless of numbering.
- Built src/analytics/correlation_heatmap.py - Pearson correlation of the same 10 core KPIs used by peer.py's RANKING_METRICS, for consistency across the project - and saved an annotated seaborn heatmap to reports/correlation_heatmap.png. Applied the same Day 34 ROE/ROCE guard before computing correlations.
- Built src/analytics/outlier_detection.py, computing a Z-score for each of the 10 core KPIs within each company's broad_sector (not across the whole market, since a normal D/E for a bank is an outlier for an FMCG company). Flagged 7 genuine outliers (9 metric flags) into output/outlier_report.csv, separate from the BEL/HAL data-bug noise which was excluded rather than flagged.
- Built src/analytics/portfolio_stats.py, computing P10/P25/P50/P75/P90/Mean/Std for the 10 core KPIs across all 92 companies' latest year, saved to output/portfolio_stats.csv - designed to be reused as-is by the Day 40 GET /api/v1/portfolio/stats endpoint.