"""
Radar Chart Generator.

Sprint 3 - Day 19

Generates radar charts for each company by comparing
its latest financial metrics against the average values
of its peer group.

Output:
    reports/radar_charts/<TICKER>_radar.png
"""

from pathlib import Path
import logging
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "radar_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Radar Metrics
# ---------------------------------------------------------------------

RADAR_METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]

RADAR_LABELS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF",
    "PAT CAGR\n5Y",
    "Revenue CAGR\n5Y",
    "Composite",
]

# ---------------------------------------------------------------------
# Database Loader
# ---------------------------------------------------------------------

def load_latest_financial_data():
    """
    Load the latest financial ratios together with peer group
    information from SQLite.
    """

    logger.info("Loading latest financial ratios...")

    with sqlite3.connect(DB_PATH) as conn:

        ratios_df = pd.read_sql(
            """
            SELECT fr.*
            FROM financial_ratios fr
            INNER JOIN (
                SELECT
                    company_id,
                    MAX(year) AS latest_year
                    FROM financial_ratios
                    GROUP BY company_id
            ) latest
                ON fr.company_id = latest.company_id
                AND fr.year = latest.latest_year
            """,
            conn,
        )

        peer_df = pd.read_sql(
            """
            SELECT *
            FROM peer_groups
            """,
            conn,
        )

    logger.info("Loaded latest financial record for each company.")
    logger.info("Financial ratios rows: %d", len(ratios_df))
    logger.info("Peer group rows: %d", len(peer_df))

    return ratios_df, peer_df

# ---------------------------------------------------------------------
# Merge Financial Ratios with Peer Groups
# ---------------------------------------------------------------------

def prepare_radar_data(ratios_df, peer_df):
    """
    Merge financial ratios with peer group information.
    """

    logger.info("Preparing radar dataset...")

    radar_df = ratios_df.merge(
        peer_df,
        on="company_id",
        how="left",
    )

    logger.info("Merged rows: %d", len(radar_df))

    return radar_df

# ---------------------------------------------------------------------
# Calculate Reference Values
# ---------------------------------------------------------------------

def calculate_reference_values(radar_df):
    """
    Calculate:

    1. Peer group averages
    2. Overall Nifty100 averages
    """

    logger.info("Calculating reference values...")

    peer_average_df = (
        radar_df
        .dropna(subset=["peer_group_name"])
        .groupby("peer_group_name")[RADAR_METRICS]
        .mean()
        .reset_index()
    )

    nifty_average = radar_df[RADAR_METRICS].mean()

    metric_min = radar_df[RADAR_METRICS].min()

    metric_max = radar_df[RADAR_METRICS].max()

    logger.info(
        "Peer groups: %d",
        len(peer_average_df),
    )

    return (
        peer_average_df,
        nifty_average,
        metric_min,
        metric_max,
    )

# ---------------------------------------------------------------------
# Get Comparison Values
# ---------------------------------------------------------------------

def get_reference_values(
    company_row,
    peer_average_df,
    nifty_average,
):
    """
    Return the appropriate comparison values for a company.

    If the company belongs to a peer group,
    use the peer-group average.

    Otherwise use the Nifty100 average.
    """

    peer_group = company_row["peer_group_name"]

    if pd.notna(peer_group):

        reference = (
            peer_average_df.loc[
                peer_average_df["peer_group_name"] == peer_group,
                RADAR_METRICS,
            ]
            .iloc[0]
        )

    else:

        reference = nifty_average

    return reference

# ---------------------------------------------------------------------
# Plot Radar Chart
# ---------------------------------------------------------------------

def plot_radar_chart(
    company_row,
    reference_values,
    metric_min,
    metric_max,
):
    """
    Plot a radar chart comparing a company with
    its peer-group average or Nifty100 average.
    """

    company_name = company_row["company_id"]

    company_series = (
        company_row[RADAR_METRICS]
        .fillna(0)
        .astype(float)
    )

    reference_series = (
        reference_values
        .fillna(0)
        .astype(float)
    )

    # ---------------------------------------------------------
    # Min-Max Normalization
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Normalize using global dataset min and max
    # ---------------------------------------------------------

    denominator = (metric_max - metric_min).replace(0, 1)

    company_values = (
        (company_series - metric_min)
        / denominator
    ).tolist()

    reference = (
        (reference_series - metric_min)
        / denominator
    ).tolist()

    num_metrics = len(RADAR_METRICS)

    angles = np.linspace(
        0,
        2 * np.pi,
        num_metrics,
        endpoint=False,
    ).tolist()

    company_values += company_values[:1]
    reference += reference[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(8, 8),
        subplot_kw=dict(polar=True),
    )

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=company_name,
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.25,
    )

    ax.plot(
        angles,
        reference,
        linestyle="--",
        linewidth=2,
        label="Reference",
    )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(RADAR_LABELS)

    ax.set_ylim(0, 1)

    ax.set_title(
        company_name,
        fontsize=14,
        pad=20,
    )

    ax.legend(loc="upper right")

    plt.tight_layout()

    output_path = OUTPUT_DIR / f"{company_name}_radar.png"

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    logger.info(
        "Saved radar chart: %s",
        output_path.name,
    )


if __name__ == "__main__":

    ratios_df, peer_df = load_latest_financial_data()

    radar_df = prepare_radar_data(
        ratios_df,
        peer_df,
    )

    (
        peer_average_df,
        nifty_average,
        metric_min,
        metric_max,
    ) = calculate_reference_values(
        radar_df,
    )

    logger.info("Generating radar charts for all companies...")

    for _, company_row in radar_df.iterrows():

        reference_values = get_reference_values(
            company_row,
            peer_average_df,
            nifty_average,
        )

        plot_radar_chart(
            company_row,
            reference_values,
            metric_min,
            metric_max,
        )

    logger.info("Finished generating all radar charts.")