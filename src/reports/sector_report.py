"""
Day 34 — Batch Report Generation (Part 2: Sector Reports)

Generates one PDF per sector (11 total) to reports/sector/{sector}_report.pdf:
  - A summary page with median KPIs across all companies in that sector
    (latest year).
  - A table listing every company in the sector with 8 metrics each:
    ROE, ROCE, Net Profit Margin, Debt-to-Equity, Revenue CAGR (5yr),
    Free Cash Flow, Composite Quality Score, Sector Relative Score.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
SECTOR_DIR = PROJECT_ROOT / "reports" / "sector"

NAVY = colors.HexColor("#1a2b4c")
LIGHT_GREY = colors.HexColor("#f0f2f5")

styles = getSampleStyleSheet()
header_style = ParagraphStyle("header", parent=styles["Normal"], fontSize=18, textColor=colors.white, leading=22)
subheader_style = ParagraphStyle("subheader", parent=styles["Normal"], fontSize=10, textColor=colors.whitesmoke)
kpi_label_style = ParagraphStyle("kpi_label", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
kpi_value_style = ParagraphStyle("kpi_value", parent=styles["Normal"], fontSize=13, textColor=colors.black, leading=15)
cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=7.5, leading=9)
header_cell_style = ParagraphStyle("header_cell", parent=styles["Normal"], fontSize=8, textColor=colors.white, leading=9)


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to the project database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def year_num_flexible(y):
    """Parses a year value in any known format into a sortable numeric form."""
    s = str(y).strip()
    m = re.search(r"(\d{4})$", s)
    if m:
        return int(m.group(1))
    m2 = re.search(r"-(\d{2})$", s)
    if m2:
        return 2000 + int(m2.group(1))
    return None


METRICS = [
    ("return_on_equity_pct", "ROE %", "{:.1f}", True),
    ("return_on_capital_employed_pct", "ROCE %", "{:.1f}", True),
    ("net_profit_margin_pct", "NPM %", "{:.1f}", False),
    ("debt_to_equity", "D/E", "{:.2f}", False),
    ("revenue_cagr_5yr", "Rev CAGR 5yr %", "{:.1f}", False),
    ("free_cash_flow_cr", "FCF (\u20b9Cr)", "{:,.0f}", False),
    ("composite_quality_score", "Quality Score", "{:.1f}", False),
    ("sector_relative_score", "Sector Rel. Score", "{:.1f}", False),
]


def load_latest_ratios_with_sector(conn):
    """Loads each company's latest financial ratios joined with sector info."""
    ratios = pd.read_sql_query(
        "SELECT fr.*, s.broad_sector FROM financial_ratios fr "
        "LEFT JOIN sectors s ON fr.company_id = s.company_id", conn
    )
    ratios["year_num"] = ratios["year"].apply(year_num_flexible)
    ratios.dropna(subset=["year_num"], inplace=True)
    ratios["year_num"] = ratios["year_num"].astype(int)
    latest = (
        ratios.sort_values("year_num")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    return latest


def fmt(value, fmt_str, is_pct_ratio_metric=False):
    """
    is_pct_ratio_metric guards against the known Sprint 2 ROE/ROCE data
    bug (e.g. BEL/HAL show values in the thousands of percent) — anything
    beyond a sane range is shown as N/A* rather than a fabricated number.
    """
    if pd.isna(value):
        return "N/A"
    if is_pct_ratio_metric and abs(value) > 200:
        return "N/A*"
    try:
        return fmt_str.format(value)
    except (ValueError, TypeError):
        return "N/A"


def sane_median(series, is_pct_ratio_metric=False):
    """Median that excludes implausible ROE/ROCE outliers from the calculation."""
    clean = series.copy()
    if is_pct_ratio_metric:
        clean = clean[clean.abs() <= 200]
    return clean.median(skipna=True)


def build_sector_pdf(sector_name, sector_df, out_path):
    """Builds the PDF report for a single sector."""
    doc = SimpleDocTemplate(
        str(out_path), pagesize=landscape(A4),
        topMargin=12 * mm, bottomMargin=12 * mm, leftMargin=12 * mm, rightMargin=12 * mm,
    )
    story = []

    # --- Header ---
    header_table = Table(
        [[Paragraph(sector_name, header_style)],
         [Paragraph(f"{len(sector_df)} companies", subheader_style)]],
        colWidths=[260 * mm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # --- Median KPI tiles ---
    median_cells = []
    for col, label, fmt_str, is_pct_ratio in METRICS[:6]:
        median_val = sane_median(sector_df[col], is_pct_ratio)
        cell = Table(
            [[Paragraph(label, kpi_label_style)], [Paragraph(fmt(median_val, fmt_str, is_pct_ratio), kpi_value_style)]],
            colWidths=[42 * mm],
        )
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        median_cells.append(cell)

    kpi_grid = Table([median_cells], colWidths=[43 * mm] * 6)
    story.append(kpi_grid)
    story.append(Spacer(1, 14))

    # --- Company table with 8 metrics ---
    header_row = [Paragraph("Ticker", header_cell_style)] + [
        Paragraph(label, header_cell_style) for _, label, _, _ in METRICS
    ]
    rows = [header_row]
    for _, row in sector_df.sort_values("company_id").iterrows():
        row_cells = [Paragraph(row["company_id"], cell_style)]
        for col, _, fmt_str, is_pct_ratio in METRICS:
            row_cells.append(Paragraph(fmt(row.get(col), fmt_str, is_pct_ratio), cell_style))
        rows.append(row_cells)

    col_widths = [26 * mm] + [(260 - 26) / 8 * mm] * 8
    company_table = Table(rows, colWidths=col_widths, repeatRows=1)
    company_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(company_table)

    doc.build(story)


def main():
    """Generates a PDF report for every sector."""
    SECTOR_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    latest = load_latest_ratios_with_sector(conn)
    conn.close()

    sectors = latest["broad_sector"].dropna().unique()
    print(f"Found {len(sectors)} sectors")

    generated = 0
    for sector_name in sorted(sectors):
        sector_df = latest[latest["broad_sector"] == sector_name]
        safe_name = re.sub(r"[^\w\-]", "_", sector_name)
        out_path = SECTOR_DIR / f"{safe_name}_report.pdf"
        build_sector_pdf(sector_name, sector_df, out_path)
        size_kb = out_path.stat().st_size / 1024
        print(f"[OK] {sector_name} ({len(sector_df)} companies) -> {out_path.name} ({size_kb:.1f} KB)")
        generated += 1

    print(f"\nGenerated {generated} sector PDFs -> {SECTOR_DIR}")


if __name__ == "__main__":
    main()