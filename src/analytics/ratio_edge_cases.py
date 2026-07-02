"""
Ratio Edge Case Validation

Sprint 2 - Day 13

Cross-check computed ROE and ROCE against
companies.xlsx reference values and log anomalies.
"""

import os
import sqlite3

import pandas as pd


DB_PATH = "nifty100.db"


def generate_ratio_edge_cases_log() -> None:
    """Generate ratio edge case log."""
    
    conn = sqlite3.connect(DB_PATH)

    financial_ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn,
    )

    companies = pd.read_sql(
        """
        SELECT
            id AS company_id,
            roe_percentage,
            roce_percentage
        FROM companies
        """,
        conn,
    )

    conn.close()

    comparison = financial_ratios.merge(
        companies,
        on="company_id",
        how="left",
    )

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(
        output_dir,
        "ratio_edge_cases.log",
    )

    with open(log_path, "w", encoding="utf-8") as log:

        log.write("RATIO EDGE CASES\n")
        log.write("=" * 70 + "\n\n")

        for _, row in comparison.iterrows():

            # -----------------------
            # ROE Validation
            # -----------------------
            if (
                pd.notna(row["roe_percentage"])
                and pd.notna(row["return_on_equity_pct"])
            ):

                difference = abs(
                    row["return_on_equity_pct"]
                    - row["roe_percentage"]
                )

                if difference > 5:

                    log.write(
                        f"[ROE] "
                        f"{row['company_id']} | "
                        f"Computed={row['return_on_equity_pct']:.2f} | "
                        f"Source={row['roe_percentage']:.2f} | "
                        f"Difference={difference:.2f}% | "
                        f"Category=DATA_SOURCE_ISSUE\n"
                    )

            # -----------------------
            # ROCE Validation
            # -----------------------
            if (
                pd.notna(row["roce_percentage"])
                and pd.notna(row["return_on_capital_employed_pct"])
            ):

                difference = abs(
                    row["return_on_capital_employed_pct"]
                    - row["roce_percentage"]
                )

                if difference > 5:

                    log.write(
                        f"[ROCE] "
                        f"{row['company_id']} | "
                        f"Computed={row['return_on_capital_employed_pct']:.2f} | "
                        f"Source={row['roce_percentage']:.2f} | "
                        f"Difference={difference:.2f}% | "
                        f"Category=VERSION_DIFFERENCE\n"
                    )

        log.write("\nValidation completed.\n")

        print("Ratio edge cases log generated successfully.")
        print(f"Log file: {log_path}")


if __name__ == "__main__":
    generate_ratio_edge_cases_log()