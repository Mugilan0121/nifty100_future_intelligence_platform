"""
Sector Analysis Screen

Select a sector, view a bubble chart (Revenue vs ROE, size = Market Cap,
color = sub-sector), and a bar chart of sector median KPIs.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_latest_ratios

st.set_page_config(page_title="Sector Analysis | Nifty 100 Analytics", layout="wide")

st.title("Sector Analysis")

df = get_latest_ratios()

if df.empty:
    st.error("No financial ratio data found.")
    st.stop()

sectors_available = sorted(df["broad_sector"].dropna().unique())
selected_sector = st.selectbox("Select Sector", sectors_available)

sector_df = df[df["broad_sector"] == selected_sector].copy()

if sector_df.empty:
    st.warning(f"No companies found for {selected_sector}.")
    st.stop()

# ---------------------------------------------------------------------
# Bubble Chart: Revenue vs ROE, size = Market Cap, color = sub-sector
# ---------------------------------------------------------------------

st.subheader(f"{selected_sector} — Revenue vs ROE")

scatter_df = sector_df.dropna(subset=["sales", "return_on_equity_pct"]).copy()

if not scatter_df.empty:
    # Market cap is used for bubble size but isn't required —
    # missing values fall back to the sector's median cap (or a flat size if none exist).
    missing_count = scatter_df["market_cap_crore"].isna().sum()

    median_cap = scatter_df["market_cap_crore"].median()
    fallback_size = median_cap if pd.notna(median_cap) else 10000.0

    scatter_df["bubble_size"] = (
        pd.to_numeric(scatter_df["market_cap_crore"], errors="coerce")
        .fillna(fallback_size)
        .astype(float)
    )

    fig_bubble = px.scatter(
        scatter_df,
        x="sales",
        y="return_on_equity_pct",
        size="bubble_size",
        color="sub_sector",
        hover_name="company_id",
        labels={
            "sales": "Revenue (₹ Cr)",
            "return_on_equity_pct": "ROE (%)",
            "bubble_size": "Market Cap (₹ Cr, est.)",
        },
        size_max=50,
    )
    fig_bubble.update_layout(height=500)
    st.plotly_chart(fig_bubble, use_container_width=True)

    if missing_count > 0:
        st.caption(
            f"⚠️ Market cap data unavailable for {missing_count} companies — "
            "shown at an estimated bubble size instead."
        )
else:
    st.info("Not enough data (revenue and ROE) to plot the bubble chart for this sector.")

st.divider()

# ---------------------------------------------------------------------
# Sector Median KPI Bar Chart
# ---------------------------------------------------------------------

st.subheader(f"{selected_sector} — Median KPIs")

median_metrics = {
    "return_on_equity_pct": "ROE (%)",
    "return_on_capital_employed_pct": "ROCE (%)",
    "net_profit_margin_pct": "Net Profit Margin (%)",
    "debt_to_equity": "Debt-to-Equity",
    "revenue_cagr_5yr": "Revenue CAGR 5yr (%)",
}

medians = {
    label: sector_df[col].median()
    for col, label in median_metrics.items()
    if col in sector_df.columns
}

fig_bar = go.Figure(
    go.Bar(
        x=list(medians.keys()),
        y=list(medians.values()),
        text=[f"{v:.1f}" for v in medians.values()],
        textposition="outside",
    )
)
fig_bar.update_layout(height=350, yaxis_title="Value")
st.plotly_chart(fig_bar, use_container_width=True)

st.caption(f"Based on {sector_df['company_id'].nunique()} companies in {selected_sector}.")