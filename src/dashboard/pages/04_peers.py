"""
Peer Comparison Screen

Select a peer group, view a radar chart of the group's average metrics
vs the benchmark company, and a side-by-side comparison table.
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_peer_groups, get_peers

st.set_page_config(page_title="Peer Comparison | Nifty 100 Analytics", layout="wide")

st.title("Peer Comparison")

peer_groups_df = get_peer_groups()

if peer_groups_df.empty:
    st.error("No peer group data found.")
    st.stop()

group_names = sorted(peer_groups_df["peer_group_name"].unique())
selected_group = st.selectbox("Select Peer Group", group_names)

peers_df = get_peers(selected_group)

if peers_df.empty:
    st.warning(f"No financial data available for companies in {selected_group}.")
    st.stop()

# ---------------------------------------------------------------------
# Radar Chart: each company's 8 metrics vs group average
# ---------------------------------------------------------------------

RADAR_METRICS = {
    "return_on_equity_pct": "ROE",
    "return_on_capital_employed_pct": "ROCE",
    "net_profit_margin_pct": "NPM",
    "debt_to_equity": "D/E (inv.)",
    "free_cash_flow_cr": "FCF",
    "pat_cagr_5yr": "PAT CAGR",
    "revenue_cagr_5yr": "Rev CAGR",
    "eps_cagr_5yr": "EPS CAGR",
}

# Normalize each metric 0-100 within the group so the radar axes are comparable
# (D/E is inverted: lower debt = better, so higher score)
radar_data = peers_df.copy()
for col in RADAR_METRICS:
    if col not in radar_data.columns:
        radar_data[col] = None

def normalize_for_radar(series, invert=False):
    """Normalizes a metric value onto a 0-1 scale for radar chart plotting."""
    valid = series.dropna()
    if valid.empty or valid.min() == valid.max():
        return series.apply(lambda x: 50 if x == x else 0)
    norm = (series - valid.min()) / (valid.max() - valid.min()) * 100
    return (100 - norm) if invert else norm

radar_scores = {}
for col in RADAR_METRICS:
    invert = (col == "debt_to_equity")
    radar_scores[col] = normalize_for_radar(radar_data[col], invert=invert)

group_avg = {col: radar_scores[col].mean() for col in RADAR_METRICS}

benchmark_row = peers_df[peers_df["is_benchmark"] == 1]
if not benchmark_row.empty:
    benchmark_ticker = benchmark_row.iloc[0]["company_id"]
    benchmark_idx = benchmark_row.index[0]
    benchmark_scores = {col: radar_scores[col].loc[benchmark_idx] for col in RADAR_METRICS}
else:
    benchmark_ticker = None
    benchmark_scores = None

axes = list(RADAR_METRICS.values())

fig = go.Figure()

fig.add_trace(go.Scatterpolar(
    r=list(group_avg.values()) + [list(group_avg.values())[0]],
    theta=axes + [axes[0]],
    fill="toself",
    name="Group Average",
))

if benchmark_scores:
    fig.add_trace(go.Scatterpolar(
        r=list(benchmark_scores.values()) + [list(benchmark_scores.values())[0]],
        theta=axes + [axes[0]],
        fill="toself",
        name=f"Benchmark ({benchmark_ticker})",
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# Side-by-side comparison table — highlight benchmark row
# ---------------------------------------------------------------------

st.subheader(f"{selected_group} — Companies")

display_cols = ["company_id", "is_benchmark"] + list(RADAR_METRICS.keys())
table_df = peers_df[display_cols].copy()
table_df = table_df.rename(columns={**RADAR_METRICS, "company_id": "Ticker", "is_benchmark": "Benchmark"})
table_df["Benchmark"] = table_df["Benchmark"].map({1: "⭐", 0: ""})

def highlight_benchmark(row):
    """Applies highlight styling to the benchmark company's row in the comparison table."""
    if row['Ticker'] == benchmark_ticker:
        return ['background-color: #fff3cd; color: #000000'] * len(row)
    return [''] * len(row)

st.dataframe(
    table_df.style.apply(highlight_benchmark, axis=1),
    use_container_width=True,
    hide_index=True,
)