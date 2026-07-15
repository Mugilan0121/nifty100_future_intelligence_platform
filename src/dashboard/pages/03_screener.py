"""
Financial Screener Screen

Sidebar sliders for 10 metrics, 6 preset buttons that auto-fill
the sliders, and a live-updating results table.
"""

import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_latest_ratios

st.set_page_config(page_title="Screener | Nifty 100 Analytics", layout="wide")

st.title("Financial Screener")

df = get_latest_ratios()

if df.empty:
    st.error("No financial ratio data found. Run the ETL pipeline first.")
    st.stop()

# ---------------------------------------------------------------------
# Preset definitions — mirrors config/screener_config.yaml thresholds
# ---------------------------------------------------------------------

PRESETS = {
    "Quality": {
        "roe_min": 15, "de_max": 1.0, "fcf_min": 0, "rev_cagr_min": 10,
        "pat_cagr_min": -30, "opm_min": -30, "pe_max": 100, "pb_max": 20.0,
        "div_yield_min": 0.0, "icr_min": 0,
    },
    "Value": {
        "roe_min": -50, "de_max": 2.0, "fcf_min": -50000, "rev_cagr_min": -30,
        "pat_cagr_min": -30, "opm_min": -30, "pe_max": 20, "pb_max": 3.0,
        "div_yield_min": 0.5, "icr_min": 0,
    },
    "Growth": {
        "roe_min": -50, "de_max": 2.0, "fcf_min": -50000, "rev_cagr_min": 15,
        "pat_cagr_min": 20, "opm_min": -30, "pe_max": 100, "pb_max": 20.0,
        "div_yield_min": 0.0, "icr_min": 0,
    },
    "Dividend": {
        "roe_min": -50, "de_max": 10.0, "fcf_min": 0, "rev_cagr_min": -30,
        "pat_cagr_min": -30, "opm_min": -30, "pe_max": 100, "pb_max": 20.0,
        "div_yield_min": 2.0, "icr_min": 0,
    },
    "Debt-Free": {
        "roe_min": 12, "de_max": 0.0, "fcf_min": -50000, "rev_cagr_min": -30,
        "pat_cagr_min": -30, "opm_min": -30, "pe_max": 100, "pb_max": 20.0,
        "div_yield_min": 0.0, "icr_min": 0,
    },
    "Turnaround": {
        "roe_min": -50, "de_max": 10.0, "fcf_min": -50000, "rev_cagr_min": 10,
        "pat_cagr_min": -30, "opm_min": -30, "pe_max": 100, "pb_max": 20.0,
        "div_yield_min": 0.0, "icr_min": 0,
    },
}

# ---------------------------------------------------------------------
# Preset buttons — set session_state, which sliders below read from
# ---------------------------------------------------------------------

st.write("**Quick Presets**")
preset_cols = st.columns(6)

for col, (name, values) in zip(preset_cols, PRESETS.items()):
    if col.button(name, use_container_width=True):
        st.session_state.update(values)

st.divider()

# ---------------------------------------------------------------------
# Sidebar: 10 metric sliders
# ---------------------------------------------------------------------

st.sidebar.header("Filter Thresholds")

roe_min = st.sidebar.slider("ROE min (%)", -50, 60, st.session_state.get("roe_min", -50))
de_max = st.sidebar.slider("D/E max", 0.0, 10.0, st.session_state.get("de_max", 10.0), step=0.1)
fcf_min = st.sidebar.slider("FCF min (₹ Cr)", -50000, 50000, st.session_state.get("fcf_min", -50000), step=500)
rev_cagr_min = st.sidebar.slider("Revenue CAGR min (5yr, %)", -30, 60, st.session_state.get("rev_cagr_min", -30))
pat_cagr_min = st.sidebar.slider("PAT CAGR min (5yr, %)", -30, 100, st.session_state.get("pat_cagr_min", -30))
opm_min = st.sidebar.slider("OPM min (%)", -30, 60, st.session_state.get("opm_min", -30))
pe_max = st.sidebar.slider("P/E max", 0, 100, st.session_state.get("pe_max", 100))
pb_max = st.sidebar.slider("P/B max", 0.0, 20.0, st.session_state.get("pb_max", 20.0), step=0.1)
div_yield_min = st.sidebar.slider("Dividend Yield min (%)", 0.0, 6.0, st.session_state.get("div_yield_min", 0.0), step=0.1)
icr_min = st.sidebar.slider("Interest Coverage min", 0, 30, st.session_state.get("icr_min", 0))

# ---------------------------------------------------------------------
# Apply Filters
# ---------------------------------------------------------------------

filtered = df.copy()

filtered = filtered[filtered["return_on_equity_pct"] >= roe_min]

# Debt-to-Equity: exclude Financial sector companies from this filter,
# same rule as your screener/engine.py apply_de_filter()
financial_mask = filtered["broad_sector"] == "Financials"
de_pass = filtered["debt_to_equity"] <= de_max
filtered = filtered[financial_mask | de_pass]

filtered = filtered[filtered["free_cash_flow_cr"] >= fcf_min]
filtered = filtered[filtered["revenue_cagr_5yr"] >= rev_cagr_min]
filtered = filtered[filtered["pat_cagr_5yr"] >= pat_cagr_min]
filtered = filtered[filtered["operating_profit_margin_pct"] >= opm_min]
filtered = filtered[filtered["pe_ratio"].isna() | (filtered["pe_ratio"] <= pe_max)]
filtered = filtered[filtered["pb_ratio"].isna() | (filtered["pb_ratio"] <= pb_max)]
filtered = filtered[filtered["dividend_yield_pct"].fillna(0) >= div_yield_min]

# Interest Coverage: debt-free companies (None/NaN) automatically pass,
# same rule as apply_icr_filter()
filtered = filtered[filtered["interest_coverage"].isna() | (filtered["interest_coverage"] >= icr_min)]

filtered = filtered.sort_values("composite_quality_score", ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------

st.subheader(f"{len(filtered)} companies match your filters")

display_cols = [
    "company_id", "company_name" if "company_name" in filtered.columns else None,
    "broad_sector", "composite_quality_score",
    "return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct",
    "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr",
    "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage",
]
display_cols = [c for c in display_cols if c and c in filtered.columns]

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------
# CSV Download
# ---------------------------------------------------------------------

csv_data = filtered[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download results as CSV",
    data=csv_data,
    file_name="screener_results.csv",
    mime="text/csv",
)   