"""
Inserts one-line docstrings for public functions currently missing one.

Sprint 6 - Day 44

Uses AST to locate each function's body precisely (handles multi-line
signatures correctly) rather than guessing based on text search.
Keyed by (relative file path, function name) since a few names like
get_connection/main/year_num_flexible repeat across files with
slightly different meanings.
"""

import ast
from pathlib import Path

# (relative path as string, function name) -> one-line docstring text
DOCSTRINGS = {
    ("src/analytics/backfill_composite_score.py", "add_score_columns_if_missing"):
        "Adds composite_quality_score and sector_relative_score columns to financial_ratios if missing.",
    ("src/analytics/backfill_composite_score.py", "backfill"):
        "Backfills composite quality scores into financial_ratios for all companies.",

    ("src/analytics/clustering.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/clustering.py", "main"):
        "Runs KMeans clustering end-to-end and writes cluster_labels.csv.",

    ("src/analytics/correlation_heatmap.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/correlation_heatmap.py", "main"):
        "Generates the KPI correlation heatmap and saves it to reports/.",

    ("src/analytics/day32_capital_allocation.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/day32_capital_allocation.py", "year_num_flexible"):
        "Parses a year value in any known format into a sortable numeric form.",
    ("src/analytics/day32_capital_allocation.py", "main"):
        "Computes capital allocation patterns for all companies and writes the output CSV.",

    ("src/analytics/generate_cashflow_intelligence.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/generate_cashflow_intelligence.py", "load_data"):
        "Loads cash flow and financial ratio data needed for cashflow intelligence metrics.",
    ("src/analytics/generate_cashflow_intelligence.py", "main"):
        "Computes cashflow intelligence KPIs for all companies and writes them to the database.",

    ("src/analytics/outlier_detection.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/outlier_detection.py", "main"):
        "Runs Z-score outlier detection across all KPIs and writes outlier_report.csv.",

    ("src/analytics/peer.py", "export_peer_comparison"):
        "Exports peer group comparison data to CSV.",
    ("src/analytics/peer.py", "main"):
        "Computes peer percentile rankings for all peer groups and writes them to the database.",

    ("src/analytics/portfolio_stats.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/analytics/portfolio_stats.py", "main"):
        "Computes portfolio-wide percentile statistics and writes portfolio_stats.csv.",

    ("src/analytics/valuation.py", "export_valuation_summary"):
        "Exports the valuation summary to valuation_summary.xlsx.",
    ("src/analytics/valuation.py", "export_valuation_flags"):
        "Exports valuation flag data to valuation_flags.csv.",

    ("src/api/db.py", "get_connection"):
        "Returns a SQLite connection to the project database with row factory enabled.",
    ("src/api/db.py", "normalize_ticker"):
        "Normalizes a ticker string to uppercase with surrounding whitespace stripped.",
    ("src/api/db.py", "company_exists"):
        "Returns True if the given ticker exists in the companies table.",
    ("src/api/db.py", "sector_exists"):
        "Returns True if the given sector name exists in the sectors table.",
    ("src/api/db.py", "peer_group_exists"):
        "Returns True if the given peer group name exists in the peer_groups table.",
    ("src/api/db.py", "pct"):
        "Returns the value at the given percentile from a pre-sorted list.",

    ("src/dashboard/pages/02_profile.py", "fmt_pct"):
        "Formats a value as a percentage string, or 'N/A' if missing.",
    ("src/dashboard/pages/02_profile.py", "fmt_ratio"):
        "Formats a ratio value, labeling zero as 'Debt Free', or 'N/A' if missing.",
    ("src/dashboard/pages/02_profile.py", "fmt_cr"):
        "Formats a value as Indian rupees in crores, or 'N/A' if missing.",

    ("src/dashboard/pages/04_peers.py", "normalize_for_radar"):
        "Normalizes a metric value onto a 0-1 scale for radar chart plotting.",
    ("src/dashboard/pages/04_peers.py", "highlight_benchmark"):
        "Applies highlight styling to the benchmark company's row in the comparison table.",

    ("src/dashboard/utils/db.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/dashboard/utils/db.py", "get_pl"):
        "Returns profit & loss history for a company.",
    ("src/dashboard/utils/db.py", "get_bs"):
        "Returns balance sheet history for a company.",
    ("src/dashboard/utils/db.py", "get_cf"):
        "Returns cash flow history for a company.",
    ("src/dashboard/utils/db.py", "get_prosandcons"):
        "Returns recorded pros and cons for a company.",
    ("src/dashboard/utils/db.py", "get_documents"):
        "Returns annual report document links for a company.",
    ("src/dashboard/utils/db.py", "get_valuation"):
        "Returns valuation summary data, optionally filtered to one company.",

    ("src/etl/load_audit.py", "get_row_count"):
        "Returns the row count for a given table.",
    ("src/etl/load_audit.py", "main"):
        "Prints row counts for all core tables as a post-load audit.",

    ("src/etl/validator.py", "log_failure"):
        "Records a single data quality failure with company, year, field, issue, and severity.",
    ("src/etl/validator.py", "save_failures"):
        "Writes all recorded failures to a CSV file and returns them as a DataFrame.",
    ("src/etl/validator.py", "validate_company_pk_uniqueness"):
        "Flags duplicate company primary keys (DQ-01).",
    ("src/etl/validator.py", "validate_annual_pk_uniqueness"):
        "Flags duplicate company/year primary keys (DQ-02).",
    ("src/etl/validator.py", "validate_company_fk"):
        "Flags rows referencing a company_id not present in the companies table (DQ-03).",
    ("src/etl/validator.py", "validate_balance_sheet_balance"):
        "Flags balance sheet rows where assets and liabilities differ by 1% or more (DQ-04).",
    ("src/etl/validator.py", "validate_opm_crosscheck"):
        "Flags rows where reported OPM diverges from calculated OPM by more than 1 point (DQ-05).",
    ("src/etl/validator.py", "validate_positive_sales"):
        "Flags rows with non-positive sales (DQ-06).",
    ("src/etl/validator.py", "validate_year_format"):
        "Flags rows whose year value isn't in YYYY-MM format (DQ-07).",
    ("src/etl/validator.py", "validate_ticker_format"):
        "Flags tickers outside the expected 2-12 character length (DQ-08).",
    ("src/etl/validator.py", "validate_net_cash_flow"):
        "Flags rows where net cash flow doesn't match operating+investing+financing within tolerance (DQ-09).",
    ("src/etl/validator.py", "validate_fixed_assets"):
        "Flags rows with negative fixed assets (DQ-10).",
    ("src/etl/validator.py", "validate_tax_rate"):
        "Flags rows with a tax rate outside the 0-60% range (DQ-11).",
    ("src/etl/validator.py", "validate_dividend_payout"):
        "Flags rows with a dividend payout ratio above 200% (DQ-12).",
    ("src/etl/validator.py", "validate_url"):
        "Flags annual report URLs that don't start with http:// or https:// (DQ-13).",
    ("src/etl/validator.py", "validate_eps_sign_consistency"):
        "Flags rows with positive net profit but non-positive EPS (DQ-14).",
    ("src/etl/validator.py", "validate_bse_ase_balance"):
        "Flags rows where total assets and total liabilities aren't exactly equal (DQ-15).",
    ("src/etl/validator.py", "validate_coverage"):
        "Flags companies present in companies but missing from the annual dataset (DQ-16).",

    ("src/nlp/parser.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/nlp/parser.py", "main"):
        "Runs the NLP regex parser against company data and writes parsed output.",

    ("src/nlp/pros_cons_generator.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/nlp/pros_cons_generator.py", "load_data"):
        "Loads the financial data needed to evaluate pros/cons rules.",
    ("src/nlp/pros_cons_generator.py", "evaluate_rules"):
        "Evaluates all pros/cons rules against a company's data and returns matching statements.",
    ("src/nlp/pros_cons_generator.py", "apply_fallbacks"):
        "Applies fallback pros/cons statements when a company has fewer than the minimum required.",
    ("src/nlp/pros_cons_generator.py", "main"):
        "Generates pros and cons for all companies and writes them to the database.",
    ("src/nlp/pros_cons_generator.py", "add"):
        "Adds a pros or cons statement with its confidence score to the results list.",

    ("src/reports/generate_all_tearsheets.py", "main"):
        "Generates a tearsheet PDF for every company in the database.",

    ("src/reports/portfolio_summary.py", "load_all_ratios"):
        "Loads the latest financial ratios for all companies.",
    ("src/reports/portfolio_summary.py", "build_kpi_tile"):
        "Builds a single KPI tile flowable for the portfolio summary PDF.",
    ("src/reports/portfolio_summary.py", "build_company_page"):
        "Builds a one-page summary section for a single company.",
    ("src/reports/portfolio_summary.py", "main"):
        "Generates the portfolio summary PDF covering all companies.",

    ("src/reports/sector_report.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/reports/sector_report.py", "year_num_flexible"):
        "Parses a year value in any known format into a sortable numeric form.",
    ("src/reports/sector_report.py", "load_latest_ratios_with_sector"):
        "Loads each company's latest financial ratios joined with sector info.",
    ("src/reports/sector_report.py", "build_sector_pdf"):
        "Builds the PDF report for a single sector.",
    ("src/reports/sector_report.py", "main"):
        "Generates a PDF report for every sector.",

    ("src/reports/tearsheet.py", "get_connection"):
        "Returns a SQLite connection to the project database.",
    ("src/reports/tearsheet.py", "year_num_flexible"):
        "Parses a year value in any known format into a sortable numeric form.",
    ("src/reports/tearsheet.py", "load_company_data"):
        "Loads all data needed to build a company's tearsheet.",
    ("src/reports/tearsheet.py", "load_pros_cons"):
        "Loads recorded pros and cons for a company.",
    ("src/reports/tearsheet.py", "load_capital_allocation_label"):
        "Loads the capital allocation pattern label for a company.",
    ("src/reports/tearsheet.py", "chart_revenue_net_profit"):
        "Builds the revenue vs net profit chart for the tearsheet.",
    ("src/reports/tearsheet.py", "chart_roe_roce"):
        "Builds the ROE vs ROCE trend chart for the tearsheet.",
    ("src/reports/tearsheet.py", "chart_balance_sheet_composition"):
        "Builds the balance sheet composition chart for the tearsheet.",
    ("src/reports/tearsheet.py", "chart_cashflow_waterfall"):
        "Builds the cash flow waterfall chart for the tearsheet.",
    ("src/reports/tearsheet.py", "fmt_ratio"):
        "Formats a ratio value, labeling zero as 'Debt Free', or 'N/A' if missing.",
    ("src/reports/tearsheet.py", "fmt_cr"):
        "Formats a value as Indian rupees in crores, or 'N/A' if missing.",
    ("src/reports/tearsheet.py", "build_kpi_table"):
        "Builds the KPI summary table flowable for the tearsheet.",
    ("src/reports/tearsheet.py", "build_header"):
        "Builds the company header section flowable for the tearsheet.",
    ("src/reports/tearsheet.py", "build_pros_cons_table"):
        "Builds the pros and cons table flowable for the tearsheet.",
    ("src/reports/tearsheet.py", "build_capital_allocation_badge"):
        "Builds the capital allocation pattern badge flowable for the tearsheet.",

    ("src/screener/engine.py", "apply_excel_formatting"):
        "Applies column widths, header styling, and conditional formatting to the exported Excel output.",
}


def process_file(rel_path: str, insertions: dict):
    path = Path(rel_path)
    if not path.exists():
        print(f"SKIP (not found): {rel_path}")
        return

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    lines = source.splitlines(keepends=True)

    to_insert = []  # (line_index_0based, indent_str, docstring_text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in insertions and ast.get_docstring(node) is None:
                if not node.body:
                    continue
                first_stmt = node.body[0]
                indent = " " * first_stmt.col_offset
                to_insert.append((first_stmt.lineno - 1, indent, insertions[node.name]))

    if not to_insert:
        return

    # Insert bottom-up so earlier line numbers stay valid
    to_insert.sort(key=lambda x: x[0], reverse=True)
    for line_idx, indent, text in to_insert:
        docstring_line = f'{indent}"""{text}"""\n'
        lines.insert(line_idx, docstring_line)

    path.write_text("".join(lines), encoding="utf-8")
    print(f"Updated {rel_path}: {len(to_insert)} docstring(s) added")


def main():
    by_file = {}
    for (rel_path, func_name), text in DOCSTRINGS.items():
        by_file.setdefault(rel_path, {})[func_name] = text

    for rel_path, insertions in by_file.items():
        process_file(rel_path, insertions)


if __name__ == "__main__":
    main()