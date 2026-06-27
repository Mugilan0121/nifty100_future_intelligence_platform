"""CAGR (Compound Annual Growth Rate) calculation utilities."""

from typing import Optional

DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def _compute_cagr(
    start_value: float,
    end_value: float,
    years: int,
) -> float:
    """Compute CAGR for valid positive values."""
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def calculate_cagr(
    start_value: float,
    end_value: float,
    years: int,
) -> tuple[Optional[float], Optional[str]]:
    """Calculate CAGR and return the CAGR value with any edge-case flag."""

    if years not in (3, 5, 10):
        return None, INSUFFICIENT

    if start_value == 0:
        return None, ZERO_BASE

    if start_value > 0 and end_value < 0:
        return None, DECLINE_TO_LOSS

    if start_value < 0 and end_value > 0:
        return None, TURNAROUND

    if start_value < 0 and end_value < 0:
        return None, BOTH_NEGATIVE

    cagr = _compute_cagr(
        start_value=start_value,
        end_value=end_value,
        years=years,
    )

    return round(cagr, 2), None


def revenue_cagr(
    start_revenue: float,
    end_revenue: float,
    years: int,
) -> tuple[Optional[float], Optional[str]]:
    """Calculate Revenue CAGR."""
    return calculate_cagr(
        start_value=start_revenue,
        end_value=end_revenue,
        years=years,
    )


def pat_cagr(
    start_profit: float,
    end_profit: float,
    years: int,
) -> tuple[Optional[float], Optional[str]]:
    """Calculate PAT CAGR."""
    return calculate_cagr(
        start_value=start_profit,
        end_value=end_profit,
        years=years,
    )


def eps_cagr(
    start_eps: float,
    end_eps: float,
    years: int,
) -> tuple[Optional[float], Optional[str]]:
    """Calculate EPS CAGR."""
    return calculate_cagr(
        start_value=start_eps,
        end_value=end_eps,
        years=years,
    )