"""
Capital Allocation Map

Treemap of all companies grouped by their capital allocation pattern
(based on CFO/CFI/CFF sign combinations). Click a pattern to see
the underlying companies.
"""

import streamlit as st
import plotly.express as px

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_capital_allocation, get_companies

st.set_page_config(page_title="Capital Allocation | Nifty 100 Analytics", layout="wide")

st.title("Capital Allocation Map")

capital_df = get_capital_allocation()

if capital_df.empty:
    st.warning(
        "No capital allocation data found. Run "
        "`python src/reports/generate_capital_allocation.py` to build "
        "`capital_allocation.csv`, then reload."
    )
    st.stop()

# ---------------------------------------------------------------------
# Use each company's most recent available year
# (fiscal year-ends differ by company — Mar, Jun, Sep, Dec —
# so there's no single shared "latest year" across all 92)
# ---------------------------------------------------------------------

year_df = (
    capital_df.sort_values("year")
    .groupby("company_id", as_index=False)
    .tail(1)
    .reset_index(drop=True)
)

st.caption(
    "Showing each company's most recent available financial year "
    "(fiscal year-end varies by company)."
)

if year_df.empty:
    st.warning("No capital allocation data available.")
    st.stop()

# ---------------------------------------------------------------------
# Treemap — grouped by pattern label
# ---------------------------------------------------------------------

pattern_counts = (
    year_df.groupby("pattern_label")
    .size()
    .reset_index(name="company_count")
)

fig = px.treemap(
    pattern_counts,
    path=["pattern_label"],
    values="company_count",
)
fig.update_traces(
    texttemplate="%{label}<br>%{value} companies",
    textfont_size=16,
)
fig.update_layout(height=500, margin=dict(t=20, b=20, l=20, r=20))

st.plotly_chart(fig, use_container_width=True)

st.caption("Click a category below to see which companies fall into that pattern.")

st.divider()

# ---------------------------------------------------------------------
# Drill-down: select a pattern, see the company list
# ---------------------------------------------------------------------

patterns_available = sorted(year_df["pattern_label"].dropna().unique())
selected_pattern = st.selectbox("Capital Allocation Pattern", patterns_available)

pattern_companies = year_df[year_df["pattern_label"] == selected_pattern]

st.subheader(f"{selected_pattern} — {len(pattern_companies)} companies")

display_cols = [c for c in ["company_id", "CFO_sign", "CFI_sign", "CFF_sign", "pattern_label"] if c in pattern_companies.columns]
st.dataframe(
    pattern_companies[display_cols],
    use_container_width=True,
    hide_index=True,
)