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

## Day 5 – Full Data Load

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

### Day 7 - Sprint Wrap-Up & Review

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
- Built 8-pattern Capital Allocation classifier using CFO, CFI and CFF cash flow signs.
- Developed 35 unit tests covering KPI calculations, classifications and capital allocation scenarios.