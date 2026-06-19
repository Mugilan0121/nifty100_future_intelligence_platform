from pathlib import Path
import pandas as pd
import re


class Validator:
    """Run data quality checks on loaded DataFrames."""

    def __init__(self):
        self.failures = []

    def log_failure(
        self,
        company_id,
        year,
        field,
        issue,
        severity,
    ):
        self.failures.append(
            {
                "company_id": company_id,
                "year": year,
                "field": field,
                "issue": issue,
                "severity": severity,
            }
        )

    def save_failures(self, output_path):
        df = pd.DataFrame(self.failures)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)

        return df

    # DQ-01 Company PK Uniqueness

    def validate_company_pk_uniqueness(
        self,
        df,
        company_col="id"
    ):
        duplicates = df[
            df.duplicated(
                subset=[company_col],
                keep=False
            )
        ]

        for _, row in duplicates.iterrows():
            self.log_failure(
                row[company_col],
                "",
                company_col,
                "Duplicate company primary key",
                "CRITICAL"
            )

    # DQ-02 Annual PK Uniqueness

    def validate_annual_pk_uniqueness(
        self,
        df,
        company_col="company_id",
        year_col="year"
    ):
        duplicates = df[
            df.duplicated(
                subset=[company_col, year_col],
                keep=False
            )
        ]

        for _, row in duplicates.iterrows():
            self.log_failure(
                row[company_col],
                row[year_col],
                f"{company_col},{year_col}",
                "Duplicate annual primary key",
                "CRITICAL"
            )

    # DQ-03 FK Integrity

    def validate_company_fk(
        self,
        df,
        companies_df,
        company_col="company_id"
    ):
        valid_ids = set(
            companies_df["id"].astype(str)
        )

        for _, row in df.iterrows():

            company_id = str(row[company_col])

            if company_id not in valid_ids:

                self.log_failure(
                    company_id,
                    row.get("year", ""),
                    company_col,
                    "Foreign key violation",
                    "CRITICAL"
                )

    # DQ-04 Balance Sheet Balance

    def validate_balance_sheet_balance(
        self,
        df
    ):
        for _, row in df.iterrows():

            total_assets = row["total_assets"]
            total_liabilities = row["total_liabilities"]

            if pd.isna(total_assets) or pd.isna(total_liabilities):
                continue

            if total_assets == 0:
                continue

            difference = abs(
                total_assets - total_liabilities
            ) / total_assets

            if difference >= 0.01:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    "total_assets,total_liabilities",
                    "Balance sheet mismatch > 1%",
                    "WARNING"
                )

    # DQ-05 OPM Cross Check

    def validate_opm_crosscheck(
        self,
        df,
        sales_col="sales",
        operating_profit_col="operating_profit",
        opm_col="opm_percentage"
    ):
        for _, row in df.iterrows():

            sales = row[sales_col]
            operating_profit = row[operating_profit_col]
            source_opm = row[opm_col]

            if pd.isna(sales) or pd.isna(operating_profit) or pd.isna(source_opm):
                continue

            if sales == 0:
                continue

            calculated_opm = (
                operating_profit / sales
            ) * 100

            if abs(calculated_opm - source_opm) > 1:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    opm_col,
                    "OPM mismatch > 1%",
                    "WARNING"
                )

    # DQ-06 Positive Sales

    def validate_positive_sales(
        self,
        df,
        sales_col="sales"
    ):
        for _, row in df.iterrows():

            sales = row[sales_col]

            if pd.isna(sales):
                continue

            if sales <= 0:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    sales_col,
                    "Sales less than or equal to zero",
                    "WARNING"
                )

    # DQ-07 Year Format

    def validate_year_format(
        self,
        df,
        year_col="year"
    ):
        pattern = r"^\d{4}-\d{2}$"

        for _, row in df.iterrows():

            value = str(row[year_col])

            if not re.match(pattern, value):

                self.log_failure(
                    row.get("company_id", ""),
                    value,
                    year_col,
                    "Invalid year format",
                    "CRITICAL"
                )

    # DQ-08 Ticker Format

    def validate_ticker_format(
        self,
        df,
        company_col="company_id"
    ):
        for _, row in df.iterrows():

            ticker = str(row[company_col])

            if len(ticker) < 2 or len(ticker) > 12:

                self.log_failure(
                    ticker,
                    row.get("year", ""),
                    company_col,
                    "Ticker length outside 2-12 characters",
                    "CRITICAL"
                )

    # DQ-09 Net Cash Flow Check

    def validate_net_cash_flow(
        self,
        df,
        operating_col="operating_activity",
        investing_col="investing_activity",
        financing_col="financing_activity",
        net_cash_col="net_cash_flow"
    ):
        for _, row in df.iterrows():

            operating = row[operating_col]
            investing = row[investing_col]
            financing = row[financing_col]
            net_cash = row[net_cash_col]

            if (
                pd.isna(operating)
                or pd.isna(investing)
                or pd.isna(financing)
                or pd.isna(net_cash)
            ):
                continue

            calculated_net_cash = (
                operating
                + investing
                + financing
            )

            difference = abs(
                net_cash - calculated_net_cash
            )

            if difference > 10:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    net_cash_col,
                    "Net cash flow mismatch > 10",
                    "WARNING"
                )

    # DQ-10 Non-Negative Fixed Assets

    def validate_fixed_assets(
        self,
        df,
        fixed_assets_col="fixed_assets"
    ):
        for _, row in df.iterrows():

            fixed_assets = row[fixed_assets_col]

            if pd.isna(fixed_assets):
                continue

            if fixed_assets < 0:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    fixed_assets_col,
                    "Negative fixed assets",
                    "WARNING"
                )

    # DQ-11 Tax Rate Range

    def validate_tax_rate(
        self,
        df,
        tax_col="tax_percentage"
    ):
        for _, row in df.iterrows():

            tax_rate = row[tax_col]

            if pd.isna(tax_rate):
                continue

            if tax_rate < 0 or tax_rate > 60:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    tax_col,
                    "Tax rate outside 0-60%",
                    "WARNING"
                )

    # DQ-12 Dividend Payout Cap

    def validate_dividend_payout(
        self,
        df,
        payout_col="dividend_payout"
    ):
        for _, row in df.iterrows():

            payout = row[payout_col]

            if pd.isna(payout):
                continue

            if payout > 200:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    payout_col,
                    "Dividend payout exceeds 200%",
                    "WARNING"
                )

    # DQ-13 URL Validity

    def validate_url(
        self,
        df,
        url_col="annual_report"
    ):
        for _, row in df.iterrows():

            url = str(row[url_col])

            if pd.isna(row[url_col]):
                continue

            if not (
                url.startswith("http://")
                or url.startswith("https://")
            ):

                self.log_failure(
                    row["company_id"],
                    "",
                    url_col,
                    "Invalid URL format",
                    "WARNING"
                )

    # DQ-14 EPS Sign Consistency

    def validate_eps_sign_consistency(
        self,
        df,
        net_profit_col="net_profit",
        eps_col="eps"
    ):
        for _, row in df.iterrows():

            net_profit = row[net_profit_col]
            eps = row[eps_col]

            if pd.isna(net_profit) or pd.isna(eps):
                continue

            if net_profit > 0 and eps <= 0:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    eps_col,
                    "Positive profit with non-positive EPS",
                    "WARNING"
                )

    # DQ-15 BSE/ASE Balance (Extended)

    def validate_bse_ase_balance(
        self,
        df
    ):
        for _, row in df.iterrows():

            total_assets = row["total_assets"]
            total_liabilities = row["total_liabilities"]

            if pd.isna(total_assets) or pd.isna(total_liabilities):
                continue

            if total_assets != total_liabilities:

                self.log_failure(
                    row["company_id"],
                    row["year"],
                    "total_assets,total_liabilities",
                    "Assets and liabilities not exactly equal",
                    "INFO"
                )

    # DQ-16 Coverage Check

    def validate_coverage(
        self,
        companies_df,
        annual_df,
        company_col="company_id"
    ):
        annual_companies = set(
            annual_df[company_col].astype(str)
        )

        for _, row in companies_df.iterrows():

            company_id = str(row["id"])

            if company_id not in annual_companies:

                self.log_failure(
                    company_id,
                    "",
                    company_col,
                    "Company missing from annual dataset",
                    "WARNING"
                )