import pytest

from src.analytics.cagr import (
    BOTH_NEGATIVE,
    DECLINE_TO_LOSS,
    INSUFFICIENT,
    TURNAROUND,
    ZERO_BASE,
    calculate_cagr,
    eps_cagr,
    pat_cagr,
    revenue_cagr,
)

def test_calculate_cagr_normal():
    """Test normal CAGR calculation."""
    result, flag = calculate_cagr(
        start_value=100,
        end_value=161.051,
        years=5,
    )

    assert round(result, 2) == 10.0
    assert flag is None

def test_calculate_cagr_zero_base():
    """Test CAGR when start value is zero."""
    result, flag = calculate_cagr(
        start_value=0,
        end_value=100,
        years=5,
    )

    assert result is None
    assert flag == ZERO_BASE

def test_calculate_cagr_decline_to_loss():
    """Test CAGR when company moves from profit to loss."""
    result, flag = calculate_cagr(
        start_value=100,
        end_value=-50,
        years=5,
    )

    assert result is None
    assert flag == DECLINE_TO_LOSS

def test_calculate_cagr_turnaround():
    """Test CAGR when company turns from loss to profit."""
    result, flag = calculate_cagr(
        start_value=-100,
        end_value=200,
        years=5,
    )

    assert result is None
    assert flag == TURNAROUND

def test_calculate_cagr_both_negative():
    """Test CAGR when both values are negative."""
    result, flag = calculate_cagr(
        start_value=-100,
        end_value=-50,
        years=5,
    )

    assert result is None
    assert flag == BOTH_NEGATIVE

def test_calculate_cagr_insufficient():
    """Test unsupported CAGR window."""
    result, flag = calculate_cagr(
        start_value=100,
        end_value=200,
        years=4,
    )

    assert result is None
    assert flag == INSUFFICIENT

def test_revenue_cagr():
    """Test Revenue CAGR wrapper."""
    result, flag = revenue_cagr(
        start_revenue=100,
        end_revenue=161.051,
        years=5,
    )

    assert round(result, 2) == 10.0
    assert flag is None

def test_pat_cagr():
    """Test PAT CAGR wrapper."""
    result, flag = pat_cagr(
        start_profit=100,
        end_profit=161.051,
        years=5,
    )

    assert round(result, 2) == 10.0
    assert flag is None

def test_eps_cagr():
    """Test EPS CAGR wrapper."""
    result, flag = eps_cagr(
        start_eps=100,
        end_eps=161.051,
        years=5,
    )

    assert round(result, 2) == 10.0
    assert flag is None

def test_calculate_cagr_three_year():
    """Test 3-year CAGR calculation."""
    result, flag = calculate_cagr(
        start_value=100,
        end_value=133.1,
        years=3,
    )

    assert round(result, 2) == 10.0
    assert flag is None
    