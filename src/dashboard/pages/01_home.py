"""
Home / Overview Screen

Shows Nifty 100 summary KPIs, sector breakdown, and top companies
by composite quality score.
"""

import streamlit as st
import plotly.express as px

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_companies, get_latest_ratios, get_sectors

st.set_page_config(page_title="Home | Nifty 100 Analytics", layout="wide")

st.title("Home / Overview")

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

try:
    companies = get_companies()
    ratios = get_latest_ratios()
    sectors = get_sectors()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

if ratios.empty:
    st.warning("No financial ratio data found. Run the ETL and ratio engine first.")
    st.stop()

# Fiscal year-ends vary by company (Mar/Jun/Sep/Dec), so there's no single
# shared "latest year" across all 92 companies. Use each company's most
# recent available year instead of filtering to one exact year string.
year_df = (
    ratios.sort_values("year")
    .groupby("company_id", as_index=False)
    .tail(1)
    .reset_index(drop=True)
)

st.sidebar.caption(
    "Showing each company's most recent available financial year "
    "(fiscal year-end varies by company)."
)

if year_df.empty:
    st.warning("No financial ratio data available.")
    st.stop()

# ---------------------------------------------------------------------
# 6 Summary KPI tiles
# ---------------------------------------------------------------------

avg_roe = year_df["return_on_equity_pct"].mean()
median_pe = year_df["pe_ratio"].median()
median_de = year_df["debt_to_equity"].median()
total_companies = year_df["company_id"].nunique()
median_rev_cagr = year_df["revenue_cagr_5yr"].median()
debt_free_count = (year_df["debt_to_equity"] == 0).sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Average ROE", f"{avg_roe:.1f}%" if avg_roe == avg_roe else "N/A")
k2.metric("Median P/E", f"{median_pe:.1f}×" if median_pe == median_pe else "N/A")
k3.metric("Median D/E", f"{median_de:.2f}" if median_de == median_de else "N/A")
k4.metric("Total Companies", total_companies)
k5.metric("Median Revenue CAGR (5yr)", f"{median_rev_cagr:.1f}%" if median_rev_cagr == median_rev_cagr else "N/A")
k6.metric("Debt-Free Companies", debt_free_count)

st.divider()

# ---------------------------------------------------------------------
# Sector breakdown donut + Top 5 companies table
# ---------------------------------------------------------------------

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Sector Breakdown")
    if not sectors.empty:
        fig = px.pie(
            sectors,
            names="broad_sector",
            values="company_count",
            hole=0.5,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector data not available.")

with col_right:
    st.subheader("Top 5 by Composite Quality Score")
    if "composite_quality_score" in year_df.columns:
        top5 = year_df.sort_values(
            "composite_quality_score", ascending=False
        ).head(5)[
            ["company_id", "broad_sector", "composite_quality_score", "return_on_equity_pct"]
        ]
        top5.columns = ["Ticker", "Sector", "Quality Score", "ROE %"]
        st.dataframe(top5, use_container_width=True, hide_index=True)
    else:
        st.info(
            "composite_quality_score column not found in financial_ratios. "
            "This is computed on the fly in the screener — see note below."
        )