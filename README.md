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