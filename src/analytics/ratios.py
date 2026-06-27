"""
Financial Ratio Engine

Sprint 2 - Day 08
-----------------
Implements profitability ratios for Nifty100 companies.

Ratios:
1. Net Profit Margin (NPM)
2. Operating Profit Margin (OPM)
3. Return on Equity (ROE)
4. Return on Capital Employed (ROCE)
5. Return on Assets (ROA)
"""

import logging
from typing import Optional


# Configure logger
logger = logging.getLogger(__name__)

def net_profit_margin(
    net_profit: float,
    sales: float
) -> Optional[float]:
    """
    Calculate Net Profit Margin (NPM).

    Formula:
        (Net Profit / Sales) * 100

    Returns:
        float : Net Profit Margin (%)
        None  : If sales is zero
    """

    if sales == 0:
        return None

    return (net_profit / sales) * 100

def operating_profit_margin(
    operating_profit: float,
    sales: float,
    source_opm: Optional[float] = None
) -> Optional[float]:
    """
    Calculate Operating Profit Margin (OPM).

    Formula:
        (Operating Profit / Sales) * 100

    If a source OPM value is provided, compare the calculated
    value against it and log a warning if the difference
    exceeds 1%.
    """

    if sales == 0:
        return None

    calculated_opm = (operating_profit / sales) * 100

    if source_opm is not None:
        difference = abs(calculated_opm - source_opm)

        if difference > 1:
            logger.warning(
                f"OPM mismatch detected. "
                f"Calculated={calculated_opm:.2f}%, "
                f"Source={source_opm:.2f}%, "
                f"Difference={difference:.2f}%"
            )

    return calculated_opm

def return_on_equity(
    net_profit: float,
    equity_capital: float,
    reserves: float
) -> Optional[float]:
    """
    Calculate Return on Equity (ROE).

    Formula:
        (Net Profit / (Equity Capital + Reserves)) * 100

    Returns:
        float : ROE (%)
        None  : If total equity is less than or equal to zero.
    """

    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return (net_profit / total_equity) * 100

def return_on_capital_employed(
    operating_profit: float,
    depreciation: float,
    equity_capital: float,
    reserves: float,
    borrowings: float
) -> Optional[float]:
    """
    Calculate Return on Capital Employed (ROCE).

    Formula:
        EBIT = Operating Profit - Depreciation

        ROCE =
        EBIT / (Equity Capital + Reserves + Borrowings) * 100

    Returns:
        float : ROCE (%)
        None  : If capital employed is zero or negative.
    """

    ebit = operating_profit - depreciation

    capital_employed = (
        equity_capital +
        reserves +
        borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100

def debt_to_equity(
    borrowings: float,
    equity_capital: float,
    reserves: float,
) -> float | None:
    """
    Calculate Debt-to-Equity Ratio.

    Formula:
        borrowings / (equity_capital + reserves)

    Edge Cases:
        - Return 0 if borrowings are 0 (debt-free company)
        - Return None if total equity is less than or equal to 0
    """

    total_equity = equity_capital + reserves

    if borrowings == 0:
        return 0

    if total_equity <= 0:
        return None

    return borrowings / total_equity

def high_leverage_flag(
    debt_to_equity: float | None,
    broad_sector: str | None,
) -> bool:
    """
    Check whether a company has excessively high leverage.

    Business Rule:
    - Financial sector companies are excluded.
    - Flag only if Debt-to-Equity > 5 for non-financial companies.
    """

    if debt_to_equity is None:
        return False

    if broad_sector is None:
        return False

    sector = broad_sector.strip().lower()

    if sector == "financials":
        return False

    return debt_to_equity > 5

def interest_coverage_ratio(
    operating_profit: float,
    other_income: float,
    interest: float,
) -> float | None:
    """
    Calculate Interest Coverage Ratio (ICR).

    Formula:
        (Operating Profit + Other Income) / Interest

    Edge Case:
        Return None if interest is zero.
    """

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest

def debt_free_label(
    interest_coverage_ratio: float | None,
) -> str:
    """
    Return a display label for Interest Coverage Ratio.
    """

    if interest_coverage_ratio is None:
        return "Debt Free"

    return f"{interest_coverage_ratio:.2f}"

def interest_coverage_warning(
    interest_coverage_ratio: float | None,
) -> bool:
    """
    Flag companies with weak interest coverage.

    Returns:
        True  -> ICR < 1.5
        False -> Otherwise
    """

    if interest_coverage_ratio is None:
        return False

    return interest_coverage_ratio < 1.5

def net_debt(
    borrowings: float,
    investments: float,
) -> float:
    """
    Calculate Net Debt.

    Formula:
        Net Debt = Borrowings - Investments

    Investments are used as a proxy for cash and liquid assets.
    """

    return borrowings - investments

def asset_turnover(
    sales: float,
    total_assets: float,
) -> float | None:
    """
    Calculate Asset Turnover Ratio.

    Formula:
        Asset Turnover = Sales / Total Assets

    Edge Case:
        Return None if total assets are zero.
    """

    if total_assets == 0:
        return None

    return sales / total_assets