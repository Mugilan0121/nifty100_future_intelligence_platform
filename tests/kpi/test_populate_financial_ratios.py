import pandas as pd

from src.analytics.populate_financial_ratios import (
    merge_tables,
    calculate_financial_ratios,
)

def sample_companies():
    return pd.DataFrame(
        {
            "company_id": ["ABC"],
            "face_value": [10],
            "book_value": [120],
        }
    )

def sample_profit_loss():
    return pd.DataFrame(
        {
            "company_id": ["ABC"],
            "year": ["2024"],
            "sales": [1000],
            "operating_profit": [250],
            "other_income": [20],
            "interest": [25],
            "net_profit": [180],
            "eps": [18],
            "dividend_payout": [30],
        }
    )

def sample_balance_sheet():
    return pd.DataFrame(
        {
            "company_id": ["ABC"],
            "year": ["2024"],
            "equity_capital": [100],
            "reserves": [500],
            "borrowings": [150],
            "total_assets": [900],
            "depreciation": [20],
        }
    )

def sample_cash_flow():
    return pd.DataFrame(
        {
            "company_id": ["ABC"],
            "year": ["2024"],
            "operating_activity": [220],
            "investing_activity": [-80],
            "financing_activity": [-40],
        }
    )

def test_merge_tables():

    merged = merge_tables(
        sample_companies(),
        sample_profit_loss(),
        sample_balance_sheet(),
        sample_cash_flow(),
    )

    assert len(merged) == 1
    assert "sales" in merged.columns
    assert "borrowings" in merged.columns
    assert "operating_activity" in merged.columns
    assert "book_value" in merged.columns

def test_calculate_financial_ratios():

    merged = merge_tables(
        sample_companies(),
        sample_profit_loss(),
        sample_balance_sheet(),
        sample_cash_flow(),
    )

    result = calculate_financial_ratios(
        merged,
    )

    assert len(result) == 1

    assert "net_profit_margin_pct" in result.columns
    assert "operating_profit_margin_pct" in result.columns
    assert "return_on_equity_pct" in result.columns

    assert "debt_to_equity" in result.columns
    assert "interest_coverage" in result.columns
    assert "asset_turnover" in result.columns

    assert "free_cash_flow_cr" in result.columns
    assert "capex_cr" in result.columns

    assert "earnings_per_share" in result.columns
    assert "book_value_per_share" in result.columns

    assert "revenue_cagr_5yr" in result.columns
    assert "pat_cagr_5yr" in result.columns
    assert "eps_cagr_5yr" in result.columns

    assert "composite_quality_score" in result.columns