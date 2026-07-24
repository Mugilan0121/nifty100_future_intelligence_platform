"""
Day 33 — PDF Tearsheet Template

Builds a 2-page company tearsheet PDF using ReportLab.

Page 1: navy header bar (company + ticker) — 6 KPI tiles (2 rows of 3) —
        10-year Revenue vs Net Profit bar chart — ROE vs ROCE dual-axis line chart
Page 2: Balance Sheet composition stacked bar — Cash Flow waterfall (latest year) —
        Pros (green bullets) — Cons (red bullets) — Capital Allocation badge

All table cells use Paragraph flowables (not raw strings) so text wraps
instead of overflowing, per the Day 33 WORDWRAP requirement.
"""

import io
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEARSHEETS_DIR = PROJECT_ROOT / "reports" / "tearsheets"

NAVY = colors.HexColor("#1a2b4c")
LIGHT_GREY = colors.HexColor("#f0f2f5")
GREEN = colors.HexColor("#1e7d32")
RED = colors.HexColor("#c62828")

styles = getSampleStyleSheet()
kpi_label_style = ParagraphStyle("kpi_label", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
kpi_value_style = ParagraphStyle("kpi_value", parent=styles["Normal"], fontSize=14, textColor=colors.black, leading=16)
header_style = ParagraphStyle("header", parent=styles["Normal"], fontSize=18, textColor=colors.white, leading=22)
subheader_style = ParagraphStyle("subheader", parent=styles["Normal"], fontSize=10, textColor=colors.whitesmoke)
section_title_style = ParagraphStyle("section_title", parent=styles["Heading3"], fontSize=12, spaceAfter=4)
pro_style = ParagraphStyle("pro", parent=styles["Normal"], fontSize=8.5, textColor=GREEN, leading=11)
con_style = ParagraphStyle("con", parent=styles["Normal"], fontSize=8.5, textColor=RED, leading=11)
badge_style = ParagraphStyle("badge", parent=styles["Normal"], fontSize=11, textColor=colors.white, alignment=1)


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


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_company_data(conn, ticker: str):
    """Loads all data needed to build a company's tearsheet."""
    company = pd.read_sql_query(
        "SELECT c.*, s.broad_sector, s.sub_sector FROM companies c "
        "LEFT JOIN sectors s ON c.id = s.company_id WHERE c.id = ?",
        conn, params=[ticker],
    )
    if company.empty:
        return None
    company_row = company.iloc[0]

    ratios = pd.read_sql_query("SELECT * FROM financial_ratios WHERE company_id = ?", conn, params=[ticker])
    pl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = ?", conn, params=[ticker])
    bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = ?", conn, params=[ticker])
    cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id = ?", conn, params=[ticker])

    for df in (ratios, pl, bs, cf):
        df["year_num"] = df["year"].apply(year_num_flexible)
        df.dropna(subset=["year_num"], inplace=True)
        df["year_num"] = df["year_num"].astype(int)
        df.sort_values("year_num", inplace=True)

    return {
        "company": company_row,
        "ratios": ratios,
        "pl": pl,
        "bs": bs,
        "cf": cf,
    }


def load_pros_cons(ticker: str):
    """Loads recorded pros and cons for a company."""
    path = OUTPUT_DIR / "pros_cons_generated.csv"
    if not path.exists():
        return [], []
    df = pd.read_csv(path)
    company_rows = df[df["company_id"] == ticker].sort_values("confidence_pct", ascending=False)
    pros = company_rows[company_rows["type"] == "pro"]["text"].tolist()
    cons = company_rows[company_rows["type"] == "con"]["text"].tolist()
    return pros, cons


def load_capital_allocation_label(ticker: str):
    """Loads the capital allocation pattern label for a company."""
    path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    if not path.exists():
        return None
    df = pd.read_excel(path)
    match = df[df["company_id"] == ticker]
    if match.empty:
        return None
    label = match.iloc[0].get("capital_allocation_label")
    return label if pd.notna(label) else None


# ---------------------------------------------------------------------
# Chart builders — matplotlib -> PNG bytes -> ReportLab Image
# ---------------------------------------------------------------------

def _fig_to_image(fig, width=170 * mm, height=70 * mm):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height)


def chart_revenue_net_profit(pl: pd.DataFrame):
    """Builds the revenue vs net profit chart for the tearsheet."""
    recent = pl.tail(10)
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    x = range(len(recent))
    width = 0.35
    ax.bar([i - width / 2 for i in x], recent["sales"], width, label="Revenue", color="#4a90d9")
    ax.bar([i + width / 2 for i in x], recent["net_profit"], width, label="Net Profit", color="#1a2b4c")
    ax.set_xticks(list(x))
    ax.set_xticklabels(recent["year_num"], rotation=45, fontsize=7)
    ax.set_title("Revenue vs Net Profit (\u20b9 Cr)", fontsize=9)
    ax.legend(fontsize=7)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


def chart_roe_roce(ratios: pd.DataFrame):
    """Builds the ROE vs ROCE trend chart for the tearsheet."""
    recent = ratios.tail(10).copy()
    # Coerce to numeric first — some rows (e.g. PNB) have a raw None rather
    # than NaN, which makes the column object-dtype and breaks .abs().
    recent["return_on_equity_pct"] = pd.to_numeric(recent["return_on_equity_pct"], errors="coerce")
    recent["return_on_capital_employed_pct"] = pd.to_numeric(recent["return_on_capital_employed_pct"], errors="coerce")

    # Guard against the known BEL/HAL-style data bug: clip implausible
    # values to NaN so a broken year doesn't compress the whole chart.
    recent.loc[recent["return_on_equity_pct"].abs() > 200, "return_on_equity_pct"] = None
    recent.loc[recent["return_on_capital_employed_pct"].abs() > 200, "return_on_capital_employed_pct"] = None

    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ax.plot(recent["year_num"], recent["return_on_equity_pct"], marker="o", color="#1a2b4c", label="ROE %", markersize=3)
    ax.plot(recent["year_num"], recent["return_on_capital_employed_pct"], marker="o", color="#c9820a", label="ROCE %", markersize=3)
    ax.set_title("ROE vs ROCE Trend (%)", fontsize=9)
    ax.legend(fontsize=7)
    ax.tick_params(axis="both", labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


def chart_balance_sheet_composition(bs: pd.DataFrame):
    """Builds the balance sheet composition chart for the tearsheet."""
    recent = bs.tail(10).copy()
    recent["equity"] = recent["equity_capital"].fillna(0) + recent["reserves"].fillna(0)
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ax.bar(recent["year_num"].astype(str), recent["equity"], label="Equity", color="#4a90d9")
    ax.bar(recent["year_num"].astype(str), recent["borrowings"], bottom=recent["equity"], label="Borrowings", color="#c62828")
    bottom2 = recent["equity"] + recent["borrowings"].fillna(0)
    ax.bar(recent["year_num"].astype(str), recent["other_liabilities"], bottom=bottom2, label="Other Liabilities", color="#9e9e9e")
    ax.set_title("Balance Sheet Composition (\u20b9 Cr)", fontsize=9)
    ax.legend(fontsize=7)
    ax.tick_params(axis="both", labelsize=7, rotation=45)
    fig.tight_layout()
    return _fig_to_image(fig)


def chart_cashflow_waterfall(cf: pd.DataFrame):
    """Builds the cash flow waterfall chart for the tearsheet."""
    if cf.empty:
        fig, ax = plt.subplots(figsize=(6.2, 2.6))
        ax.text(0.5, 0.5, "No cash flow data available", ha="center", va="center", fontsize=9)
        ax.axis("off")
        return _fig_to_image(fig)

    latest = cf.iloc[-1]
    cfo, cfi, cff, net = (
        latest["operating_activity"], latest["investing_activity"],
        latest["financing_activity"], latest["net_cash_flow"],
    )
    labels = ["CFO", "CFI", "CFF", "Net Cash Flow"]
    values = [cfo, cfi, cff, net]
    colors_list = ["#1e7d32" if v >= 0 else "#c62828" for v in values]

    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ax.bar(labels, values, color=colors_list)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title(f"Cash Flow Waterfall — {int(latest['year_num'])} (\u20b9 Cr)", fontsize=9)
    ax.tick_params(axis="both", labelsize=7)
    fig.tight_layout()
    return _fig_to_image(fig)


# ---------------------------------------------------------------------
# KPI helpers
# ---------------------------------------------------------------------

def fmt_pct(v):
    """
    Guards against implausible ROE/ROCE values (a known Sprint 2 data bug
    affecting a small number of companies, e.g. BEL/HAL, where
    financial_ratios has values in the thousands of percent instead of
    tens). Anything beyond a sane range is shown as N/A* rather than
    displayed as a fabricated number.
    """
    v = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
    if pd.isna(v):
        return "N/A"
    if abs(v) > 200:
        return "N/A*"
    return f"{v:.1f}%"


def fmt_ratio(v):
    """Formats a ratio value, labeling zero as 'Debt Free', or 'N/A' if missing."""
    if pd.isna(v):
        return "N/A"
    return "Debt Free" if v == 0 else f"{v:.2f}"


def fmt_cr(v):
    """Formats a value as Indian rupees in crores, or 'N/A' if missing."""
    return f"\u20b9{v:,.0f} Cr" if pd.notna(v) else "N/A"


def build_kpi_table(latest_ratios):
    """Builds the KPI summary table flowable for the tearsheet."""
    kpis = [
        ("ROE", fmt_pct(latest_ratios.get("return_on_equity_pct"))),
        ("ROCE", fmt_pct(latest_ratios.get("return_on_capital_employed_pct"))),
        ("Net Profit Margin", fmt_pct(latest_ratios.get("net_profit_margin_pct"))),
        ("Debt-to-Equity", fmt_ratio(latest_ratios.get("debt_to_equity"))),
        ("Revenue CAGR (5yr)", fmt_pct(latest_ratios.get("revenue_cagr_5yr"))),
        ("Free Cash Flow", fmt_cr(latest_ratios.get("free_cash_flow_cr"))),
    ]

    cells = []
    for label, value in kpis:
        cell = Table(
            [[Paragraph(label, kpi_label_style)], [Paragraph(value, kpi_value_style)]],
            colWidths=[56 * mm],
        )
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        cells.append(cell)

    row1 = cells[:3]
    row2 = cells[3:]
    kpi_grid = Table([row1, row2], colWidths=[58 * mm] * 3, spaceAfter=6)
    kpi_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return kpi_grid


def build_header(company_name, ticker, sector):
    """Builds the company header section flowable for the tearsheet."""
    header_table = Table(
        [[Paragraph(f"{company_name}", header_style)],
         [Paragraph(f"{ticker} \u00b7 {sector or 'N/A'}", subheader_style)]],
        colWidths=[180 * mm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return header_table


def build_pros_cons_table(pros, cons, max_items=6):
    """Builds the pros and cons table flowable for the tearsheet."""
    pro_paras = [Paragraph(f"\u2713 {p}", pro_style) for p in pros[:max_items]] or [Paragraph("No pros recorded.", pro_style)]
    con_paras = [Paragraph(f"\u2717 {c}", con_style) for c in cons[:max_items]] or [Paragraph("No cons recorded.", con_style)]

    max_len = max(len(pro_paras), len(con_paras))
    pro_paras += [Paragraph("", pro_style)] * (max_len - len(pro_paras))
    con_paras += [Paragraph("", con_style)] * (max_len - len(con_paras))

    rows = [[Paragraph("Pros", section_title_style), Paragraph("Cons", section_title_style)]]
    rows += [[p, c] for p, c in zip(pro_paras, con_paras)]

    table = Table(rows, colWidths=[86 * mm, 86 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def build_capital_allocation_badge(label):
    """Builds the capital allocation pattern badge flowable for the tearsheet."""
    label_display = (label or "N/A").replace("_", " ").title()
    badge_color = {
        "Reinvestor": colors.HexColor("#1e7d32"),
        "Growth Financing": colors.HexColor("#4a90d9"),
        "Shareholder Returns": colors.HexColor("#1e7d32"),
        "Cash Accumulation": colors.HexColor("#1e7d32"),
        "Cash Burn": colors.HexColor("#c9820a"),
        "Distress": colors.HexColor("#c62828"),
        "Asset Liquidation": colors.HexColor("#c9820a"),
        "External Funding": colors.HexColor("#c9820a"),
    }.get(label_display, colors.grey)

    badge = Table([[Paragraph(f"Capital Allocation: {label_display}", badge_style)]], colWidths=[172 * mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return badge


# ---------------------------------------------------------------------
# Main tearsheet builder
# ---------------------------------------------------------------------

def build_tearsheet(ticker: str, output_path: Path) -> bool:
    """Returns True if built successfully, False if skipped (insufficient data)."""
    conn = get_connection()
    data = load_company_data(conn, ticker)
    conn.close()

    if data is None or data["ratios"].empty:
        return False

    ratios = data["ratios"]
    if len(ratios) < 3:
        return False  # Day 34 will skip companies with <3 years of data

    latest_ratios = ratios.iloc[-1]
    company = data["company"]
    pros, cons = load_pros_cons(ticker)
    capital_allocation_label = load_capital_allocation_label(ticker)

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        topMargin=14 * mm, bottomMargin=14 * mm, leftMargin=14 * mm, rightMargin=14 * mm,
    )
    story = []

    # --- Page 1 ---
    story.append(build_header(company["company_name"], ticker, company.get("broad_sector")))
    story.append(Spacer(1, 10))
    story.append(build_kpi_table(latest_ratios))
    story.append(Spacer(1, 10))

    if not data["pl"].empty:
        story.append(chart_revenue_net_profit(data["pl"]))
    story.append(Spacer(1, 6))

    if not ratios.empty:
        story.append(chart_roe_roce(ratios))

    story.append(PageBreak())

    # --- Page 2 ---
    if not data["bs"].empty:
        story.append(chart_balance_sheet_composition(data["bs"]))
    story.append(Spacer(1, 6))

    story.append(chart_cashflow_waterfall(data["cf"]))
    story.append(Spacer(1, 10))

    story.append(build_pros_cons_table(pros, cons))
    story.append(Spacer(1, 10))

    story.append(build_capital_allocation_badge(capital_allocation_label))

    doc.build(story)
    return True


if __name__ == "__main__":
    TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)

    # Day 33 test set — 5 companies across different sectors
    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]

    for ticker in test_tickers:
        out_path = TEARSHEETS_DIR / f"{ticker}_tearsheet.pdf"
        ok = build_tearsheet(ticker, out_path)
        if ok:
            size_kb = out_path.stat().st_size / 1024
            print(f"[OK] {ticker} -> {out_path.name} ({size_kb:.1f} KB)")
        else:
            print(f"[SKIP] {ticker} — insufficient data")