"""
Day 35 — Portfolio Summary PDF

Generates reports/portfolio/portfolio_summary.pdf — one page per company,
alphabetical by ticker, showing the same 6 KPIs used throughout the
project (ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF) plus a trend arrow
comparing the latest year to the previous year.

Trend arrow rules (not fully specified in the brief — documented here):
  - ROE, ROCE, NPM, Revenue CAGR (percentage-scale metrics): flat if the
    change is within 2 percentage points; otherwise up if increased,
    down if decreased.
  - D/E: lower is better, so "improved" means a DECREASE. Flat if the
    change is within 0.02 (absolute), matching the "within 2%" spirit
    for a ratio rather than a percentage.
  - FCF (₹ Cr): flat if the RELATIVE change is within 2% (an absolute
    ₹2 threshold wouldn't be meaningful across companies of very
    different scale); otherwise up/down based on relative change.

Reuses fmt_pct/fmt_ratio/fmt_cr from tearsheet.py, which already include
the Day 34 ROE/ROCE sanity guard (N/A* for implausible values).
"""

import sqlite3
from pathlib import Path

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

from tearsheet import get_connection, year_num_flexible, fmt_pct, fmt_ratio, fmt_cr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_DIR = PROJECT_ROOT / "reports" / "portfolio"

NAVY = colors.HexColor("#1a2b4c")
LIGHT_GREY = colors.HexColor("#f0f2f5")
GREEN = colors.HexColor("#1e7d32")
RED = colors.HexColor("#c62828")
GREY = colors.HexColor("#757575")

styles = getSampleStyleSheet()
header_style = ParagraphStyle("header", parent=styles["Normal"], fontSize=18, textColor=colors.white, leading=22)
subheader_style = ParagraphStyle("subheader", parent=styles["Normal"], fontSize=10, textColor=colors.whitesmoke)
kpi_label_style = ParagraphStyle("kpi_label", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
kpi_value_style = ParagraphStyle("kpi_value", parent=styles["Normal"], fontSize=14, leading=16)

UP_ARROW = "\u25b2"
DOWN_ARROW = "\u25bc"
FLAT_ARROW = "\u25b6"

GREEN_HEX = "1e7d32"
RED_HEX = "c62828"
GREY_HEX = "757575"

# (column, display label, format_fn, higher_is_better, flat_threshold, threshold_is_relative)
KPI_CONFIG = [
    ("return_on_equity_pct", "ROE", fmt_pct, True, 2.0, False),
    ("return_on_capital_employed_pct", "ROCE", fmt_pct, True, 2.0, False),
    ("net_profit_margin_pct", "Net Profit Margin", fmt_pct, True, 2.0, False),
    ("debt_to_equity", "Debt-to-Equity", fmt_ratio, False, 0.02, False),
    ("revenue_cagr_5yr", "Revenue CAGR (5yr)", fmt_pct, True, 2.0, False),
    ("free_cash_flow_cr", "Free Cash Flow", fmt_cr, True, 2.0, True),
]


def load_all_ratios(conn):
    """Loads the latest financial ratios for all companies."""
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    ratios["year_num"] = ratios["year"].apply(year_num_flexible)
    ratios.dropna(subset=["year_num"], inplace=True)
    ratios["year_num"] = ratios["year_num"].astype(int)
    ratios.sort_values(["company_id", "year_num"], inplace=True)
    return ratios


def compute_trend(latest_val, prev_val, higher_is_better, flat_threshold, relative):
    """Returns (arrow_char, hex_color_str) or (None, GREY_HEX) if not comparable."""
    if pd.isna(latest_val) or pd.isna(prev_val):
        return None, GREY_HEX

    diff = latest_val - prev_val
    if relative:
        if prev_val == 0:
            return None, GREY_HEX
        change = abs(diff) / abs(prev_val) * 100
    else:
        change = abs(diff)

    if change <= flat_threshold:
        return FLAT_ARROW, GREY_HEX

    improved = (diff > 0) if higher_is_better else (diff < 0)
    return (UP_ARROW, GREEN_HEX) if improved else (DOWN_ARROW, RED_HEX)


def build_kpi_tile(label, value_text, arrow, arrow_color_hex):
    """Builds a single KPI tile flowable for the portfolio summary PDF."""
    if arrow:
        value_para = Paragraph(
            f'{value_text} <font color="#{arrow_color_hex}">{arrow}</font>',
            kpi_value_style,
        )
    else:
        value_para = Paragraph(value_text, kpi_value_style)

    cell = Table(
        [[Paragraph(label, kpi_label_style)], [value_para]],
        colWidths=[56 * mm],
    )
    cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return cell


def build_company_page(company_id, company_name, sector, latest_row, prev_row):
    """Builds a one-page summary section for a single company."""
    story = []

    header_table = Table(
        [[Paragraph(company_name, header_style)],
         [Paragraph(f"{company_id} \u00b7 {sector or 'N/A'}", subheader_style)]],
        colWidths=[180 * mm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    cells = []
    for col, label, fmt_fn, higher_is_better, threshold, relative in KPI_CONFIG:
        latest_val = latest_row.get(col) if latest_row is not None else None
        prev_val = prev_row.get(col) if prev_row is not None else None
        value_text = fmt_fn(latest_val)
        arrow, arrow_color_hex = (None, GREY_HEX)
        if prev_row is not None:
            arrow, arrow_color_hex = compute_trend(latest_val, prev_val, higher_is_better, threshold, relative)
        cells.append(build_kpi_tile(label, value_text, arrow, arrow_color_hex))

    row1, row2 = cells[:3], cells[3:]
    kpi_grid = Table([row1, row2], colWidths=[58 * mm] * 3)
    kpi_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpi_grid)

    legend = Paragraph(
        f'<font color="#1e7d32">{UP_ARROW} improved</font> &nbsp;&nbsp; '
        f'<font color="#c62828">{DOWN_ARROW} declined</font> &nbsp;&nbsp; '
        f'<font color="#757575">{FLAT_ARROW} flat (within threshold)</font> vs. prior year',
        ParagraphStyle("legend", parent=styles["Normal"], fontSize=7, textColor=colors.grey),
    )
    story.append(Spacer(1, 10))
    story.append(legend)

    return story


def main():
    """Generates the portfolio summary PDF covering all companies."""
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    companies = pd.read_sql_query(
        "SELECT c.id AS company_id, c.company_name, s.broad_sector FROM companies c "
        "LEFT JOIN sectors s ON c.id = s.company_id ORDER BY c.id",
        conn,
    )
    ratios = load_all_ratios(conn)
    conn.close()

    out_path = PORTFOLIO_DIR / "portfolio_summary.pdf"
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        topMargin=14 * mm, bottomMargin=14 * mm, leftMargin=14 * mm, rightMargin=14 * mm,
    )

    story = []
    included = 0
    skipped = []

    for i, row in companies.iterrows():
        company_id = row["company_id"]
        company_hist = ratios[ratios["company_id"] == company_id]

        if company_hist.empty:
            skipped.append(company_id)
            continue

        latest_row = company_hist.iloc[-1]
        prev_row = company_hist.iloc[-2] if len(company_hist) >= 2 else None

        page_story = build_company_page(
            company_id, row["company_name"], row["broad_sector"], latest_row, prev_row
        )
        story.extend(page_story)
        story.append(PageBreak())
        included += 1

    # Remove trailing page break
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)

    size_kb = out_path.stat().st_size / 1024
    print(f"Generated portfolio_summary.pdf with {included} company pages ({size_kb:.1f} KB) -> {out_path}")
    if skipped:
        print(f"Skipped {len(skipped)} companies with no financial_ratios data: {skipped}")


if __name__ == "__main__":
    main()