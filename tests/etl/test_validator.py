import sys
from pathlib import Path
import pandas as pd

sys.path.append(
    str(Path(__file__).resolve().parents[2])
)

from src.etl.validator import Validator

v = Validator()

# DQ-01 Company PK Uniqueness

companies_pk = pd.DataFrame(
    {
        "id": [
            "TCS",
            "INFY",
            "TCS"
        ]
    }
)

v.validate_company_pk_uniqueness(companies_pk)

# DQ-02 Annual PK Uniqueness

annual_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03",
            "2024-03"
        ]
    }
)

v.validate_annual_pk_uniqueness(annual_df)

# DQ-03 FK Integrity

companies_master = pd.DataFrame(
    {
        "id": [
            "TCS",
            "INFY"
        ]
    }
)

fk_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "ABC",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03",
            "2024-03"
        ]
    }
)

v.validate_company_fk(
    fk_df,
    companies_master
)

# DQ-04 Balance Sheet Balance

balance_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "total_assets": [
            1000,
            1000
        ],
        "total_liabilities": [
            995,
            700
        ]
    }
)

v.validate_balance_sheet_balance(balance_df)

# DQ-05 OPM Cross Check

opm_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "sales": [
            1000,
            1000
        ],
        "operating_profit": [
            200,
            300
        ],
        "opm_percentage": [
            20,
            10
        ]
    }
)

v.validate_opm_crosscheck(opm_df)

# DQ-06 Positive Sales

sales_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "sales": [
            100,
            -50
        ]
    }
)

v.validate_positive_sales(sales_df)

# DQ-07 Year Format

year_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "Mar-24",
            "2023"
        ]
    }
)

v.validate_year_format(year_df)

# DQ-08 Ticker Format

ticker_df = pd.DataFrame(
    {
        "company_id": [
            "A",
            "ABCDEFGHIJKLMN"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ]
    }
)

v.validate_ticker_format(ticker_df)

# DQ-09 Net Cash Flow Check

cashflow_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "operating_activity": [
            100,
            100
        ],
        "investing_activity": [
            -20,
            -20
        ],
        "financing_activity": [
            -10,
            -10
        ],
        "net_cash_flow": [
            70,
            200
        ]
    }
)

v.validate_net_cash_flow(cashflow_df)

# DQ-10 Non-Negative Fixed Assets

fixed_assets_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "fixed_assets": [
            1000,
            -500
        ]
    }
)

v.validate_fixed_assets(
    fixed_assets_df
)

# DQ-11 Tax Rate Range

tax_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "tax_percentage": [
            25,
            75
        ]
    }
)

v.validate_tax_rate(
    tax_df
)

# DQ-12 Dividend Payout Cap

dividend_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "dividend_payout": [
            50,
            250
        ]
    }
)

v.validate_dividend_payout(
    dividend_df
)

# DQ-13 URL Validity

url_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "annual_report": [
            "https://www.tcs.com/report.pdf",
            "www.infy.com/report.pdf"
        ]
    }
)

v.validate_url(
    url_df
)

# DQ-14 EPS Sign Consistency

eps_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "net_profit": [
            1000,
            1000
        ],
        "eps": [
            50,
            -5
        ]
    }
)

v.validate_eps_sign_consistency(
    eps_df
)

# DQ-15 BSE/ASE Balance (Extended)

bse_ase_df = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ],
        "year": [
            "2024-03",
            "2024-03"
        ],
        "total_assets": [
            1000,
            1000
        ],
        "total_liabilities": [
            1000,
            995
        ]
    }
)

v.validate_bse_ase_balance(
    bse_ase_df
)

# DQ-16 Coverage Check

coverage_companies = pd.DataFrame(
    {
        "id": [
            "TCS",
            "INFY",
            "WIPRO"
        ]
    }
)

coverage_annual = pd.DataFrame(
    {
        "company_id": [
            "TCS",
            "INFY"
        ]
    }
)

v.validate_coverage(
    coverage_companies,
    coverage_annual
)

# SAVE RESULTS

print(
    v.save_failures(
        "output/validation_failures.csv"
    )
)

