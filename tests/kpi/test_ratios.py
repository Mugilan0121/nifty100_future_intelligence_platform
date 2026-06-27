import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    debt_free_label,
    interest_coverage_warning,
    net_debt,
    asset_turnover,
)


def test_net_profit_margin():
    """Test normal Net Profit Margin calculation."""
    result = net_profit_margin(
        net_profit=250,
        sales=1000,
    )
    assert result == 25.0


def test_net_profit_margin_zero_sales():
    """Should return None when sales is zero."""
    result = net_profit_margin(
        net_profit=100,
        sales=0,
    )
    assert result is None


def test_operating_profit_margin():
    """Test normal OPM calculation."""
    result = operating_profit_margin(
        operating_profit=300,
        sales=1000,
        source_opm=30,
    )
    assert result == 30.0


def test_operating_profit_margin_zero_sales():
    """Should return None when sales is zero."""
    result = operating_profit_margin(
        operating_profit=200,
        sales=0,
    )
    assert result is None


def test_return_on_equity():
    """Test normal ROE calculation."""
    result = return_on_equity(
        net_profit=300,
        equity_capital=1000,
        reserves=2000,
    )
    assert result == 10.0


def test_return_on_equity_negative_equity():
    """ROE should return None for non-positive equity."""
    result = return_on_equity(
        net_profit=100,
        equity_capital=-500,
        reserves=200,
    )
    assert result is None


def test_return_on_capital_employed():
    """Test normal ROCE calculation."""
    result = return_on_capital_employed(
        operating_profit=500,
        depreciation=100,
        equity_capital=1000,
        reserves=2000,
        borrowings=1000,
    )
    assert result == 10.0


def test_return_on_capital_employed_zero_capital():
    """ROCE should return None when capital employed is zero."""
    result = return_on_capital_employed(
        operating_profit=500,
        depreciation=100,
        equity_capital=0,
        reserves=0,
        borrowings=0,
    )
    assert result is None

# Day 9 - Leverage & Efficiency Ratio Tests

def test_debt_to_equity():
    """Normal Debt-to-Equity calculation."""
    result = debt_to_equity(
        borrowings=500,
        equity_capital=200,
        reserves=300,
    )
    assert result == 1.0


def test_debt_to_equity_debt_free():
    """Debt-free companies should return 0."""
    result = debt_to_equity(
        borrowings=0,
        equity_capital=500,
        reserves=1000,
    )
    assert result == 0


def test_interest_coverage_zero_interest():
    """ICR should return None when interest is zero."""
    result = interest_coverage_ratio(
        operating_profit=1000,
        other_income=200,
        interest=0,
    )
    assert result is None


def test_debt_free_label():
    """Debt-free companies should display 'Debt Free'."""
    assert debt_free_label(None) == "Debt Free"


def test_high_leverage_flag():
    """Non-financial companies with D/E > 5 should be flagged."""
    assert high_leverage_flag(6.5, "Industrials") is True


def test_interest_coverage_warning():
    """Companies with ICR < 1.5 should be flagged."""
    assert interest_coverage_warning(1.2) is True


def test_net_debt():
    """Net Debt = Borrowings - Investments."""
    result = net_debt(
        borrowings=1000,
        investments=300,
    )
    assert result == 700


def test_asset_turnover():
    """Normal Asset Turnover calculation."""
    result = asset_turnover(
        sales=1200,
        total_assets=600,
    )
    assert result == 2.0