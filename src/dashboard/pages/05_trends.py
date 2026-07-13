"""
Trend Analysis Screen

Search a company, select up to 3 metrics, and view a 10-year
overlay line chart with YoY % change annotations.
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis | Nifty 100 Analytics", layout="wide")

st.title("Trend Analysis")

companies = get_companies()

if companies.empty:
    st.error("No company data found.")
    st.stop()

companies["display_label"] = companies["id"] + " — " + companies["company_name"]

search_input = st.selectbox(
    "Search by company name or ticker",
    options=companies["display_label"].sort_values(),
    index=None,
    placeholder="Start typing a ticker or company name...",
)

if search_input is None:
    st.info("Select a company to view its trends.")
    st.stop()

ticker = search_input.split(" — ")[0].strip()

AVAILABLE_METRICS = {
    "return_on_equity_pct": "ROE (%)",
    "return_on_capital_employed_pct": "ROCE (%)",
    "net_profit_margin_pct": "Net Profit Margin (%)",
    "debt_to_equity": "Debt-to-Equity",
    "free_cash_flow_cr": "Free Cash Flow (₹ Cr)",
    "revenue_cagr_5yr": "Revenue CAGR 5yr (%)",
    "pat_cagr_5yr": "PAT CAGR 5yr (%)",
    "asset_turnover": "Asset Turnover",
}

selected_metrics = st.multiselect(
    "Select up to 3 metrics to overlay",
    options=list(AVAILABLE_METRICS.keys()),
    format_func=lambda x: AVAILABLE_METRICS[x],
    max_selections=3,
    default=["return_on_equity_pct"],
)

if not selected_metrics:
    st.info("Select at least one metric.")
    st.stop()

history = get_ratios(ticker=ticker).sort_values("year")

if history.empty:
    st.warning(f"No historical data available for {ticker}.")
    st.stop()

history = history.tail(10)

# Metrics that are ratios (small scale, 0-10ish) get the secondary axis;
# percentage metrics (ROE, ROCE, NPM, CAGRs) share the primary axis.
RATIO_METRICS = {"debt_to_equity", "asset_turnover"}

fig = go.Figure()

for metric in selected_metrics:
    if metric not in history.columns:
        continue

    values = history[metric]
    yoy_change = values.pct_change() * 100

    hover_text = [
        f"{AVAILABLE_METRICS[metric]}: {v:.2f}<br>YoY: {c:+.1f}%" if c == c
        else f"{AVAILABLE_METRICS[metric]}: {v:.2f}<br>YoY: N/A"
        for v, c in zip(values, yoy_change)
    ]

    fig.add_trace(go.Scatter(
        x=history["year"],
        y=values,
        name=AVAILABLE_METRICS[metric],
        mode="lines+markers",
        hovertext=hover_text,
        hoverinfo="text",
        yaxis="y2" if metric in RATIO_METRICS else "y1",
    ))

fig.update_layout(
    title=f"{ticker} — 10-Year Trend",
    height=500,
    hovermode="closest",
    yaxis=dict(title="Percentage (%)"),
    yaxis2=dict(title="Ratio", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)

st.plotly_chart(fig, use_container_width=True)