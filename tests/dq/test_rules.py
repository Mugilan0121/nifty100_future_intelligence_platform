"""
Unit tests for src/etl/validator.py's 16 DQ rules.

Sprint 6 - Day 41

Each test builds a DataFrame that violates exactly one rule and checks
that Validator logs a failure with the correct field and severity.
Note: the validator has 16 rules (DQ-01 to DQ-16), not the 14 the
sprint plan mentions - all 16 are tested here. There is no literal
"rule_id" field in log_failure()'s output (it records field/issue/
severity) so these tests check field + severity, not a rule_id string.
"""

import pandas as pd
import pytest

from src.etl.validator import Validator


@pytest.fixture
def validator():
    return Validator()


# DQ-01 Company PK Uniqueness

def test_dq01_company_pk_uniqueness_flags_duplicate(validator):
    df = pd.DataFrame({"id": ["TCS", "INFY", "TCS"]})
    validator.validate_company_pk_uniqueness(df)
    assert len(validator.failures) == 2
    assert all(f["severity"] == "CRITICAL" for f in validator.failures)
    assert all(f["field"] == "id" for f in validator.failures)


# DQ-02 Annual PK Uniqueness

def test_dq02_annual_pk_uniqueness_flags_duplicate(validator):
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2024-03", "2024-03", "2024-03"],
    })
    validator.validate_annual_pk_uniqueness(df)
    assert len(validator.failures) == 2
    assert validator.failures[0]["severity"] == "CRITICAL"
    assert validator.failures[0]["field"] == "company_id,year"


# DQ-03 FK Integrity

def test_dq03_company_fk_flags_invalid_reference(validator):
    companies = pd.DataFrame({"id": ["TCS", "INFY"]})
    df = pd.DataFrame({
        "company_id": ["TCS", "ABC", "INFY"],
        "year": ["2024-03", "2024-03", "2024-03"],
    })
    validator.validate_company_fk(df, companies)
    assert len(validator.failures) == 1
    assert validator.failures[0]["company_id"] == "ABC"
    assert validator.failures[0]["severity"] == "CRITICAL"


# DQ-04 Balance Sheet Balance

def test_dq04_balance_sheet_flags_mismatch_over_1pct(validator):
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "total_assets": [1000],
        "total_liabilities": [700],
    })
    validator.validate_balance_sheet_balance(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "total_assets,total_liabilities"


def test_dq04_balance_sheet_no_failure_under_1pct(validator):
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2024-03"],
        "total_assets": [1000],
        "total_liabilities": [995],
    })
    validator.validate_balance_sheet_balance(df)
    assert len(validator.failures) == 0


# DQ-05 OPM Cross Check

def test_dq05_opm_crosscheck_flags_mismatch(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "sales": [1000],
        "operating_profit": [300],
        "opm_percentage": [10],  # actual = 30%, mismatch > 1
    })
    validator.validate_opm_crosscheck(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "opm_percentage"


# DQ-06 Positive Sales

def test_dq06_positive_sales_flags_non_positive(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "sales": [-50],
    })
    validator.validate_positive_sales(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "sales"


# DQ-07 Year Format

def test_dq07_year_format_flags_invalid(validator):
    df = pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["Mar-24", "2023"],  # neither matches YYYY-MM
    })
    validator.validate_year_format(df)
    assert len(validator.failures) == 2
    assert all(f["severity"] == "CRITICAL" for f in validator.failures)


# DQ-08 Ticker Format

def test_dq08_ticker_format_flags_out_of_range_length(validator):
    df = pd.DataFrame({
        "company_id": ["A", "ABCDEFGHIJKLMN"],  # 1 char, 14 chars
        "year": ["2024-03", "2024-03"],
    })
    validator.validate_ticker_format(df)
    assert len(validator.failures) == 2
    assert all(f["severity"] == "CRITICAL" for f in validator.failures)


# DQ-09 Net Cash Flow Check

def test_dq09_net_cash_flow_flags_mismatch_over_10(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "operating_activity": [100],
        "investing_activity": [-20],
        "financing_activity": [-10],
        "net_cash_flow": [200],  # calculated = 70, diff = 130
    })
    validator.validate_net_cash_flow(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "net_cash_flow"


# DQ-10 Non-Negative Fixed Assets

def test_dq10_fixed_assets_flags_negative(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "fixed_assets": [-500],
    })
    validator.validate_fixed_assets(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "fixed_assets"


# DQ-11 Tax Rate Range

def test_dq11_tax_rate_flags_out_of_range(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "tax_percentage": [75],  # > 60
    })
    validator.validate_tax_rate(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "tax_percentage"


# DQ-12 Dividend Payout Cap

def test_dq12_dividend_payout_flags_excess(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "dividend_payout": [250],  # > 200
    })
    validator.validate_dividend_payout(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "dividend_payout"


# DQ-13 URL Validity

def test_dq13_url_flags_invalid_format(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "annual_report": ["www.infy.com/report.pdf"],  # no http(s)://
    })
    validator.validate_url(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "annual_report"


# DQ-14 EPS Sign Consistency

def test_dq14_eps_sign_consistency_flags_mismatch(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "net_profit": [1000],
        "eps": [-5],  # positive profit, non-positive EPS
    })
    validator.validate_eps_sign_consistency(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "WARNING"
    assert validator.failures[0]["field"] == "eps"


# DQ-15 BSE/ASE Balance (Extended)

def test_dq15_bse_ase_balance_flags_not_exactly_equal(validator):
    df = pd.DataFrame({
        "company_id": ["INFY"],
        "year": ["2024-03"],
        "total_assets": [1000],
        "total_liabilities": [995],
    })
    validator.validate_bse_ase_balance(df)
    assert len(validator.failures) == 1
    assert validator.failures[0]["severity"] == "INFO"
    assert validator.failures[0]["field"] == "total_assets,total_liabilities"


# DQ-16 Coverage Check

def test_dq16_coverage_flags_missing_company(validator):
    companies = pd.DataFrame({"id": ["TCS", "INFY", "WIPRO"]})
    annual = pd.DataFrame({"company_id": ["TCS", "INFY"]})
    validator.validate_coverage(companies, annual)
    assert len(validator.failures) == 1
    assert validator.failures[0]["company_id"] == "WIPRO"
    assert validator.failures[0]["severity"] == "WARNING"


# save_failures() sanity check

def test_save_failures_writes_csv(validator, tmp_path):
    df = pd.DataFrame({"id": ["TCS", "TCS"]})
    validator.validate_company_pk_uniqueness(df)
    out_path = tmp_path / "output" / "validation_failures.csv"
    result_df = validator.save_failures(out_path)
    assert out_path.exists()
    assert len(result_df) == 2
    assert list(result_df.columns) == ["company_id", "year", "field", "issue", "severity"]