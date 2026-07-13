"""
Company Profile Screen

Search for a company by ticker or name, view its profile card,
KPI tiles, financial trend charts, and pros/cons.
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_companies, get_ratios, get_pl, get_bs, get_prosandcons

st.set_page_config(page_title="Company Profile | Nifty 100 Analytics", layout="wide")

st.title("Company Profile")

# ---------------------------------------------------------------------
# Load company list once (cached) for the search/autocomplete
# ---------------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("No company data found. Run the ETL pipeline first.")
    st.stop()

# Build a "TCS — Tata Consultancy Services Ltd" style label per company
companies["display_label"] = companies["id"] + " — " + companies["company_name"]

search_input = st.selectbox(
    "Search by company name or ticker",
    options=companies["display_label"].sort_values(),
    index=None,
    placeholder="Start typing a ticker or company name...",
)

if search_input is None:
    st.info("Select a company above to view its profile.")
    st.stop()

ticker = search_input.split(" — ")[0].strip()
company_row = companies[companies["id"] == ticker].iloc[0]

# ---------------------------------------------------------------------
# Company Card
# ---------------------------------------------------------------------

card_col1, card_col2 = st.columns([1, 3])

with card_col1:
    if company_row.get("company_logo"):
        try:
            st.image(company_row["company_logo"], width=100)
        except Exception:
            st.write("🏢")

with card_col2:
    st.subheader(company_row["company_name"])
    st.caption(
        f"**{company_row['broad_sector']}** · {company_row['sub_sector']} · "
        f"NSE: {company_row['id']}"
    )
    if company_row.get("about_company"):
        st.write(company_row["about_company"])

st.divider()

# ---------------------------------------------------------------------
# 6 KPI Tiles — latest year data
# ---------------------------------------------------------------------

ratios_history = get_ratios(ticker=ticker)

if ratios_history.empty:
    st.warning(f"No financial ratio data available for {ticker}.")
    st.stop()

latest = ratios_history.sort_values("year").iloc[-1]

k1, k2, k3, k4, k5, k6 = st.columns(6)

def fmt_pct(value):
    return f"{value:.1f}%" if value == value else "N/A"

def fmt_ratio(value):
    if value != value:
        return "N/A"
    return "Debt Free" if value == 0 else f"{value:.2f}"

def fmt_cr(value):
    return f"₹{value:,.0f} Cr" if value == value else "N/A"

k1.metric("ROE", fmt_pct(latest["return_on_equity_pct"]))
k2.metric("ROCE", fmt_pct(latest["return_on_capital_employed_pct"]))
k3.metric("Net Profit Margin", fmt_pct(latest["net_profit_margin_pct"]))
k4.metric("Debt-to-Equity", fmt_ratio(latest["debt_to_equity"]))
k5.metric("Revenue CAGR (5yr)", fmt_pct(latest["revenue_cagr_5yr"]))
k6.metric("Free Cash Flow", fmt_cr(latest["free_cash_flow_cr"]))

st.divider()

# ---------------------------------------------------------------------
# 10-Year Revenue & Net Profit Bar Chart
# ---------------------------------------------------------------------

pl_history = get_pl(ticker)

if not pl_history.empty:
    pl_recent = pl_history.tail(10)

    fig_pl = go.Figure()
    fig_pl.add_bar(x=pl_recent["year"], y=pl_recent["sales"], name="Revenue")
    fig_pl.add_bar(x=pl_recent["year"], y=pl_recent["net_profit"], name="Net Profit")
    fig_pl.update_layout(
        title="Revenue vs Net Profit (₹ Cr)",
        barmode="group",
        height=400,
        margin=dict(t=40, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_pl, use_container_width=True)
else:
    st.info("No Profit & Loss history available.")

# ---------------------------------------------------------------------
# ROE vs ROCE Dual-Axis Line Chart (10-year)
# ---------------------------------------------------------------------

ratios_recent = ratios_history.sort_values("year").tail(10)

if not ratios_recent.empty:
    fig_roe = go.Figure()
    fig_roe.add_trace(
        go.Scatter(
            x=ratios_recent["year"],
            y=ratios_recent["return_on_equity_pct"],
            name="ROE %",
            mode="lines+markers",
        )
    )
    fig_roe.add_trace(
        go.Scatter(
            x=ratios_recent["year"],
            y=ratios_recent["return_on_capital_employed_pct"],
            name="ROCE %",
            mode="lines+markers",
        )
    )
    fig_roe.update_layout(
        title="ROE vs ROCE Trend (10yr)",
        height=350,
        margin=dict(t=40, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_roe, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# Pros & Cons
# ---------------------------------------------------------------------

prosandcons = get_prosandcons(ticker)

pc_col1, pc_col2 = st.columns(2)

with pc_col1:
    st.subheader("✅ Pros")
    pros = prosandcons["pros"].dropna().tolist() if not prosandcons.empty else []
    if pros:
        for item in pros:
            st.markdown(f"- {item}")
    else:
        st.caption("No pros recorded for this company yet.")

with pc_col2:
    st.subheader("❌ Cons")
    cons = prosandcons["cons"].dropna().tolist() if not prosandcons.empty else []
    if cons:
        for item in cons:
            st.markdown(f"- {item}")
    else:
        st.caption("No cons recorded for this company yet.")