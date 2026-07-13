"""
Nifty 100 Analytics — Streamlit entry point.

Run with: streamlit run src/dashboard/app.py
Individual screens live in pages/ and are auto-discovered by Streamlit.
"""

import streamlit as st
from utils.db import get_companies, get_latest_ratios

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Nifty 100 Financial Intelligence Platform")

st.markdown(
    """
    A financial analytics platform covering **92 Nifty 100 companies** — built on a
    ratio engine of 50+ computed KPIs, a multi-preset investment screener,
    peer benchmarking across 11 groups, and sector-level analytics.

    Every number here is computed from raw P&L, Balance Sheet, and Cash Flow
    statements — not scraped ratios — so it's fully traceable back to source data.
    """
)

try:
    companies = get_companies()
    ratios = get_latest_ratios()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies Tracked", len(companies))
    col2.metric("Sectors", companies["broad_sector"].nunique())
    col3.metric("Peer Groups", 11)
    col4.metric("Latest Data Year", ratios["year"].max() if not ratios.empty else "N/A")

    st.success("Database connected. Select a screen from the sidebar to begin.")

    st.divider()

    st.subheader("What's in the sidebar")

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        st.markdown(
            """
            - **Home** — Nifty 100 summary KPIs and sector breakdown
            - **Profile** — deep dive on a single company: KPIs, trends, pros/cons
            - **Screener** — filter all 92 companies against 10 custom thresholds
            - **Peers** — radar comparison against peer group benchmarks
            """
        )

    with nav_col2:
        st.markdown(
            """
            - **Trends** — 10-year metric history for any company
            - **Sectors** — revenue/ROE bubble chart and sector medians
            - **Capital** — how companies allocate cash (reinvest, distress, etc.)
            - **Reports** — annual report archive with live link validation
            """
        )

    st.caption(
        "Built with Python, pandas, SQLite, and Streamlit · "
        "Data covers FY2010–2024 across profitability, leverage, growth, and cash flow metrics."
    )

except FileNotFoundError as e:
    st.error(str(e))
    st.info("Run `python src/etl/loader.py` (or `make load`) to build the database first.")