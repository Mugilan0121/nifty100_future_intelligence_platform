"""
Populate the financial_ratios table.

Sprint 2 - Day 12
"""

import sqlite3
import pandas as pd

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src" / "analytics"))

from ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover,
)

from cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)

from cashflow_kpis import (
    free_cash_flow,
)   

from quality_score import composite_quality_score

DB_PATH = "nifty100.db"

def load_tables():
    """Load required tables from SQLite."""

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)
    print(companies.columns.tolist())

    profit_loss = pd.read_sql(
        "SELECT * FROM profitandloss",
        conn,
    )

    balance_sheet = pd.read_sql(
        "SELECT * FROM balancesheet",
        conn,
    )

    cash_flow = pd.read_sql(
        "SELECT * FROM cashflow",
        conn,
    )

    conn.close()

    return companies, profit_loss, balance_sheet, cash_flow

def merge_tables(
    companies: pd.DataFrame,
    profit_loss: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cash_flow: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge Companies, Profit & Loss, Balance Sheet and Cash Flow tables.
    """

    # Rename id -> company_id
    companies = companies.rename(
        columns={
            "id": "company_id"
        }
    )

    # Merge Profit & Loss + Balance Sheet
    merged = profit_loss.merge(
        balance_sheet,
        on=["company_id", "year"],
        how="inner",
    )

    # Merge Cash Flow
    merged = merged.merge(
        cash_flow,
        on=["company_id", "year"],
        how="inner",
    )

    # Add company information
    merged = merged.merge(
        companies[
            [
                "company_id",
                "face_value",
                "book_value",
                "roe_percentage",
                "roce_percentage",
            ]
        ],
        on="company_id",
        how="left",
    )

    return merged

def calculate_financial_ratios(
    merged: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate all financial KPIs for each company-year.
    """

    merged = merged.sort_values(
        by=["company_id", "year"]
    )

    results = []

    for _, row in merged.iterrows():

        # -----------------------------
        # Profitability Ratios
        # -----------------------------
        npm = net_profit_margin(
            net_profit=row["net_profit"],
            sales=row["sales"],
        )

        opm = operating_profit_margin(
            operating_profit=row["operating_profit"],
            sales=row["sales"],
        )

        roe = return_on_equity(
            net_profit=row["net_profit"],
            equity_capital=row["equity_capital"],
            reserves=row["reserves"],
        )

        roec = return_on_capital_employed(
            operating_profit=row["operating_profit"],
            depreciation=row["depreciation"],
            equity_capital=row["equity_capital"],
            reserves=row["reserves"],
            borrowings=row["borrowings"],
        )

        # -----------------------------
        # Leverage Ratios
        # -----------------------------
        de_ratio = debt_to_equity(
            borrowings=row["borrowings"],
            equity_capital=row["equity_capital"],
            reserves=row["reserves"],
        )

        icr = interest_coverage_ratio(
            operating_profit=row["operating_profit"],
            other_income=row["other_income"],
            interest=row["interest"],
        )

        # -----------------------------
        # Efficiency Ratio
        # -----------------------------
        turnover = asset_turnover(
            sales=row["sales"],
            total_assets=row["total_assets"],
        )

        # -----------------------------
        # Cash Flow KPIs
        # -----------------------------
        fcf = free_cash_flow(
            operating_activity=row["operating_activity"],
            investing_activity=row["investing_activity"],
        )

        capex = abs(row["investing_activity"])

        

        # -----------------------------
        # CAGR KPIs
        # -----------------------------

        revenue_growth = None
        pat_growth = None
        eps_growth = None

        company_history = merged[
            merged["company_id"] == row["company_id"]
        ].reset_index(drop=True)

        current_index = company_history[
            company_history["year"] == row["year"]
        ].index

        if len(current_index) > 0 and current_index[0] >= 5:

            previous = company_history.iloc[
                current_index[0] - 5
            ]

            revenue_growth, _ = revenue_cagr(
                start_revenue=previous["sales"],
                end_revenue=row["sales"],
                years=5,
            )

            pat_growth, _ = pat_cagr(
                start_profit=previous["net_profit"],
                end_profit=row["net_profit"],
                years=5,
            )

            eps_growth, _ = eps_cagr(
                start_eps=previous["eps"],
                end_eps=row["eps"],
                years=5,
            )

                    # -----------------------------
        # Composite Quality Score
        # -----------------------------
        composite_score = 0

        if npm is not None:
            composite_score += npm

        if roe is not None:
            composite_score += roe

        if de_ratio is not None:
            composite_score -= de_ratio

        if revenue_growth is not None:
            composite_score += revenue_growth

        if pat_growth is not None:
            composite_score += pat_growth

        if eps_growth is not None:
            composite_score += eps_growth

        # -----------------------------
        # Store Results
        # -----------------------------
        results.append(
            {
                "company_id": row["company_id"],
                "year": row["year"],

                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "return_on_capital_employed_pct":roec,

                "debt_to_equity": de_ratio,
                "interest_coverage": icr,
                "asset_turnover": turnover,

                "free_cash_flow_cr": fcf,
                "capex_cr": capex,

                "earnings_per_share": row["eps"],
                "book_value_per_share": row["book_value"],

                "dividend_payout_ratio_pct": row["dividend_payout"],

                "total_debt_cr": row["borrowings"],

                "cash_from_operations_cr": row["operating_activity"],

# CAGR KPIs (to implement next)
"revenue_cagr_5yr": revenue_growth,
"pat_cagr_5yr": pat_growth,
"eps_cagr_5yr": eps_growth,

# Composite quality score
"composite_quality_score": round(composite_score, 2),

            }
        )

    return pd.DataFrame(results)



if __name__ == "__main__":

    companies, pl, bs, cf = load_tables()

    merged = merge_tables(
        companies,
        pl,
        bs,
        cf,
    )

    ratios_df = calculate_financial_ratios(
        merged,
    )

    conn = sqlite3.connect(DB_PATH)

    ratios_df.to_sql(
        "financial_ratios",
        conn,
        if_exists="replace",
        index=False,
    )

    conn.close()

    print("Financial ratios inserted successfully.")
    print("Rows inserted:", len(ratios_df))