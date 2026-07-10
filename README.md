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