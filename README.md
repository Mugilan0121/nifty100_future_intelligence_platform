# Nifty 100 Financial Intelligence Platform

Financial Intelligence Platform for 92 Nifty 100 companies.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

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