# Nifty 100 Future Intelligence Platform

A financial analytics platform covering all 92 Nifty 100 listed companies — ETL, financial ratio computation, screening, peer benchmarking, sector analytics, NLP-driven insights, PDF reporting, ML clustering, statistical analysis, and a REST API.

Full day-by-day build history is in [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md). For usage instructions (not development), see [docs/analyst_guide.pdf](docs/analyst_guide.pdf).

## Stack

Python · SQLite · pandas · scikit-learn · FastAPI · Streamlit · ReportLab · matplotlib · seaborn

## Project Structure

src/
etl/ - Excel loading, normalization, data quality validation
analytics/ - Financial ratios, CAGR, cash flow KPIs, clustering, peer analysis
screener/ - Configurable financial screener engine
nlp/ - Regex-based text parsing, pros/cons generation
reports/ - PDF tearsheets, sector reports, portfolio summary
api/ - FastAPI REST server
dashboard/ - Streamlit application (8 screens)
tests/ - pytest suite (etl/, kpi/, dq/, api/)
config/ - Screener preset configuration
docs/ - Analyst guide, development log, generated reports
output/ - Generated CSVs, Excel exports, performance notes
reports/ - Generated PDFs, charts

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the ETL Pipeline

Loads all source Excel files into `nifty100.db`, then computes financial ratios, screener outputs, peer percentiles, clustering, cashflow intelligence, and pros/cons:

```bash
python src/etl/loader.py
python src/analytics/populate_financial_ratios.py
python src/analytics/backfill_composite_score.py
```

See `docs/DEVELOPMENT_LOG.md` for the full ETL/analytics pipeline order if regenerating all derived outputs from scratch.

## Running the Dashboard

```bash
streamlit run src/dashboard/app.py --server.port 8501
```

Opens at `http://localhost:8501`.

## Running the API

```bash
uvicorn src.api.main:app --port 8000
```

Interactive API docs (Swagger UI) at `http://localhost:8000/docs`. See `docs/analyst_guide.pdf` for example `curl` commands per endpoint.

The dashboard and API can run simultaneously — they use separate ports (8501 and 8000) and do not conflict.

## Running the Test Suite

```bash
pytest tests/ --html=reports/pytest_report.html -v
```

Current status: 163+ tests passing across ETL, KPI, data quality, and API layers. See `docs/DEVELOPMENT_LOG.md` for test coverage details by module.

## Generating PDF Reports

```bash
python src/reports/generate_all_tearsheets.py      # one tearsheet per company
python src/reports/sector_report.py                # one report per sector
python src/reports/portfolio_summary.py            # single portfolio-wide PDF
```

## Known Issues

- `financial_ratios` ROE/ROCE values are corrupted for BEL and HAL (Sprint 2 ratio engine bug) — display-layer sanity guard applied (±200%, shown as `N/A*`), not patched at source. Flagged for team lead review.
- The dataset contains 10 distinct sectors, not the 11 referenced in the original sprint plan.
- 8 companies have financial data but are absent from `companies` metadata (Sprint 1 scope mismatch).
- `NHPC`'s `company_name` contains an embedded newline character; flagged for ETL cleanup.
- Full list of known data-quality flags: `output/validation_failures.csv`. Performance characteristics: `output/perf_notes.md`.