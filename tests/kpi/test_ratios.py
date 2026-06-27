import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
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