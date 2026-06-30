import pytest

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    classify_cfo_quality,
    capex_intensity,
    classify_capex_intensity,
    fcf_conversion_rate,
    classify_fcf_conversion,
    capital_allocation_pattern,
    HIGH_QUALITY,
    MODERATE,
    ACCRUAL_RISK,
    ASSET_LIGHT,
    CAPITAL_MODERATE,
    CAPITAL_INTENSIVE,
    EFFICIENT,
    AVERAGE,
    CAPEX_HEAVY,
    REINVESTOR,
    GROWTH_FINANCING,
    SHAREHOLDER_RETURNS,
    CASH_ACCUMULATION,
    CASH_BURN,
    DISTRESS,
    ASSET_LIQUIDATION,
    EXTERNAL_FUNDING,
)

def test_free_cash_flow_positive():
    """Test Free Cash Flow with positive result."""
    result = free_cash_flow(
        operating_activity=500,
        investing_activity=-200,
    )

    assert result == 300


def test_free_cash_flow_negative():
    """Test Free Cash Flow with negative result."""
    result = free_cash_flow(
        operating_activity=500,
        investing_activity=-700,
    )

    assert result == -200


def test_free_cash_flow_zero():
    """Test Free Cash Flow with zero values."""
    result = free_cash_flow(
        operating_activity=0,
        investing_activity=0,
    )

    assert result == 0

def test_cfo_quality_score_high():
    """Test CFO Quality Score greater than 1."""
    result = cfo_quality_score(
        operating_activity=120,
        net_profit=100,
    )

    assert result == 1.2


def test_cfo_quality_score_moderate():
    """Test CFO Quality Score between 0.5 and 1."""
    result = cfo_quality_score(
        operating_activity=75,
        net_profit=100,
    )

    assert result == 0.75


def test_cfo_quality_score_low():
    """Test CFO Quality Score below 0.5."""
    result = cfo_quality_score(
        operating_activity=30,
        net_profit=100,
    )

    assert result == 0.3


def test_cfo_quality_score_zero_pat():
    """Return None when PAT is zero."""
    result = cfo_quality_score(
        operating_activity=100,
        net_profit=0,
    )

    assert result is None


def test_classify_cfo_quality_high():
    """Test High Quality classification."""
    assert classify_cfo_quality(1.2) == HIGH_QUALITY


def test_classify_cfo_quality_moderate():
    """Test Moderate classification."""
    assert classify_cfo_quality(0.75) == MODERATE


def test_classify_cfo_quality_low():
    """Test Accrual Risk classification."""
    assert classify_cfo_quality(0.3) == ACCRUAL_RISK


def test_classify_cfo_quality_none():
    """Return None for missing score."""
    assert classify_cfo_quality(None) is None

def test_capex_intensity_asset_light():
    """Test Asset Light CapEx Intensity."""
    result = capex_intensity(
        investing_activity=-20,
        sales=1000,
    )

    assert result == 2.0


def test_capex_intensity_moderate():
    """Test Moderate CapEx Intensity."""
    result = capex_intensity(
        investing_activity=-50,
        sales=1000,
    )

    assert result == 5.0


def test_capex_intensity_capital_intensive():
    """Test Capital Intensive CapEx Intensity."""
    result = capex_intensity(
        investing_activity=-100,
        sales=1000,
    )

    assert result == 10.0


def test_capex_intensity_zero_sales():
    """Return None when sales is zero."""
    result = capex_intensity(
        investing_activity=-50,
        sales=0,
    )

    assert result is None


def test_classify_capex_asset_light():
    """Test Asset Light classification."""
    assert classify_capex_intensity(2.0) == ASSET_LIGHT


def test_classify_capex_moderate():
    """Test Moderate classification."""
    assert classify_capex_intensity(5.0) == CAPITAL_MODERATE


def test_classify_capex_capital_intensive():
    """Test Capital Intensive classification."""
    assert classify_capex_intensity(10.0) == CAPITAL_INTENSIVE


def test_classify_capex_none():
    """Return None for missing CapEx Intensity."""
    assert classify_capex_intensity(None) is None

def test_fcf_conversion_efficient():
    """Test Efficient FCF Conversion."""
    result = fcf_conversion_rate(
        free_cash_flow=80,
        operating_profit=100,
    )

    assert result == 80.0


def test_fcf_conversion_average():
    """Test Average FCF Conversion."""
    result = fcf_conversion_rate(
        free_cash_flow=50,
        operating_profit=100,
    )

    assert result == 50.0


def test_fcf_conversion_capex_heavy():
    """Test CapEx Heavy FCF Conversion."""
    result = fcf_conversion_rate(
        free_cash_flow=20,
        operating_profit=100,
    )

    assert result == 20.0


def test_fcf_conversion_zero_operating_profit():
    """Return None when operating profit is zero."""
    result = fcf_conversion_rate(
        free_cash_flow=50,
        operating_profit=0,
    )

    assert result is None


def test_classify_fcf_conversion_efficient():
    """Test Efficient classification."""
    assert classify_fcf_conversion(80.0) == EFFICIENT


def test_classify_fcf_conversion_average():
    """Test Average classification."""
    assert classify_fcf_conversion(50.0) == AVERAGE


def test_classify_fcf_conversion_capex_heavy():
    """Test CapEx Heavy classification."""
    assert classify_fcf_conversion(20.0) == CAPEX_HEAVY


def test_classify_fcf_conversion_none():
    """Return None for missing conversion rate."""
    assert classify_fcf_conversion(None) is None

def test_capital_allocation_reinvestor():
    """Test Reinvestor pattern."""
    assert (
        capital_allocation_pattern(100, -50, -20)
        == REINVESTOR
    )


def test_capital_allocation_growth_financing():
    """Test Growth Through Financing pattern."""
    assert (
        capital_allocation_pattern(100, -50, 20)
        == GROWTH_FINANCING
    )


def test_capital_allocation_shareholder_returns():
    """Test Shareholder Returns pattern."""
    assert (
        capital_allocation_pattern(100, 50, -20)
        == SHAREHOLDER_RETURNS
    )


def test_capital_allocation_cash_accumulation():
    """Test Cash Accumulation pattern."""
    assert (
        capital_allocation_pattern(100, 50, 20)
        == CASH_ACCUMULATION
    )


def test_capital_allocation_cash_burn():
    """Test Cash Burn pattern."""
    assert (
        capital_allocation_pattern(-100, -50, -20)
        == CASH_BURN
    )


def test_capital_allocation_distress():
    """Test Distress pattern."""
    assert (
        capital_allocation_pattern(-100, -50, 20)
        == DISTRESS
    )


def test_capital_allocation_asset_liquidation():
    """Test Asset Liquidation pattern."""
    assert (
        capital_allocation_pattern(-100, 50, -20)
        == ASSET_LIQUIDATION
    )


def test_capital_allocation_external_funding():
    """Test External Funding pattern."""
    assert (
        capital_allocation_pattern(-100, 50, 20)
        == EXTERNAL_FUNDING
    )