"""
Peer Percentile Rankings.

Sprint 3 - Day 18

Loads peer groups and computes percentile rankings
within each peer group.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "nifty100.db"

PEER_GROUPS_PATH = (
    PROJECT_ROOT
    / "data"
    / "supporting"
    / "peer_groups.xlsx"
)

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Metrics to Rank
# ---------------------------------------------------------------------

RANKING_METRICS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

# ---------------------------------------------------------------------
# Load Peer Groups
# ---------------------------------------------------------------------

def load_peer_groups():
    """
    Load peer group assignments from Excel.
    """

    peer_df = pd.read_excel(PEER_GROUPS_PATH)

    logger.info(
        "Loaded %d peer group assignments.",
        len(peer_df)
    )

    return peer_df

# ---------------------------------------------------------------------
# Load Financial Ratios
# ---------------------------------------------------------------------

def load_financial_ratios(conn):
    """
    Load financial ratios from SQLite.
    """

    query = """
    SELECT *
    FROM financial_ratios
    """

    ratios_df = pd.read_sql(query, conn)

    logger.info(
        "Loaded %d financial ratio records.",
        len(ratios_df)
    )

    return ratios_df

# ---------------------------------------------------------------------
# Create SQLite Table
# ---------------------------------------------------------------------

def create_peer_percentiles_table(conn):
    """
    Create peer_percentiles table.
    """

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (

            company_id TEXT,

            peer_group_name TEXT,

            metric TEXT,

            value REAL,

            percentile_rank REAL,

            year TEXT
        )
    """)

    conn.commit()

    logger.info("peer_percentiles table created successfully.")

# ---------------------------------------------------------------------
# Merge Peer Groups with Financial Ratios
# ---------------------------------------------------------------------

def calculate_peer_percentiles(peer_df, ratios_df):
    """
    Merge peer group assignments with financial ratios.
    """

    merged_df = ratios_df.merge(
        peer_df[
            [
                "company_id",
                "peer_group_name",
            ]
        ],
        on="company_id",
        how="left",
    )

    # Handle companies not assigned to a peer group
    merged_df["peer_group_name"] = merged_df[
        "peer_group_name"
    ].fillna("No peer group assigned")

    results = []

    valid_peer_df = merged_df[
        merged_df["peer_group_name"] !=
        "No peer group assigned"
    ].copy()

    for peer_group, group_df in valid_peer_df.groupby(
        "peer_group_name"
    ):
     
     for metric in RANKING_METRICS:

        percentile = group_df[metric].rank(
             pct=True,
             method="average",
         )

        if metric == "debt_to_equity":
             percentile = 1 - percentile

        for index, row in group_df.iterrows():

            results.append(
                {
                    "company_id": row["company_id"],
                    "peer_group_name": row["peer_group_name"],
                    "metric": metric,
                    "value": row[metric],
                    "percentile_rank": percentile.loc[index],
                    "year": row["year"],
                }
            )
    
    percentile_df = pd.DataFrame(results)

    logger.info(
        "Calculated %d percentile records.",
        len(percentile_df),
    )   

    return percentile_df

# ---------------------------------------------------------------------
# Save Percentiles
# ---------------------------------------------------------------------

def save_peer_percentiles(conn, percentile_df):
    """
    Save percentile rankings into SQLite.
    """

    cursor = conn.cursor()

    # Clear existing records
    cursor.execute("DELETE FROM peer_percentiles")

    percentile_df.to_sql(
        "peer_percentiles",
        conn,
        if_exists="append",
        index=False,
    )

    conn.commit()

    logger.info(
        "Saved %d percentile records to peer_percentiles table.",
        len(percentile_df),
    )

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    conn = sqlite3.connect(DATABASE_PATH)

    create_peer_percentiles_table(conn)

    peer_df = load_peer_groups()

    ratios_df = load_financial_ratios(conn)

    percentile_df = calculate_peer_percentiles(
        peer_df,
        ratios_df,
    )

    save_peer_percentiles(
        conn,
        percentile_df,
    )

    print("\nPeer Percentiles")
    print(percentile_df.head(15))

    conn.close()


if __name__ == "__main__":
    main()

