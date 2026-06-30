"""Cash Flow KPI calculation utilities."""

from typing import Optional

# CFO Quality classifications
HIGH_QUALITY = "HIGH_QUALITY"
MODERATE = "MODERATE"
ACCRUAL_RISK = "ACCRUAL_RISK"

# CapEx Intensity classifications
ASSET_LIGHT = "ASSET_LIGHT"
CAPITAL_MODERATE = "CAPITAL_MODERATE"
CAPITAL_INTENSIVE = "CAPITAL_INTENSIVE"

# FCF Conversion classifications
EFFICIENT = "EFFICIENT"
AVERAGE = "AVERAGE"
CAPEX_HEAVY = "CAPEX_HEAVY"

# Capital Allocation Patterns
REINVESTOR = "REINVESTOR"
GROWTH_FINANCING = "GROWTH_FINANCING"
SHAREHOLDER_RETURNS = "SHAREHOLDER_RETURNS"
CASH_ACCUMULATION = "CASH_ACCUMULATION"
CASH_BURN = "CASH_BURN"
DISTRESS = "DISTRESS"
ASSET_LIQUIDATION = "ASSET_LIQUIDATION"
EXTERNAL_FUNDING = "EXTERNAL_FUNDING"

def free_cash_flow(
    operating_activity: float,
    investing_activity: float,
) -> float:
    """
    Calculate Free Cash Flow (FCF).

    Formula:
        FCF = Operating Activity + Investing Activity
    """
    return operating_activity + investing_activity

def cfo_quality_score(
    operating_activity: float,
    net_profit: float,
) -> Optional[float]:
    """
    Calculate CFO Quality Score.

    Formula:
        CFO Quality = Operating Activity / Net Profit
    """

    if net_profit == 0:
        return None

    return operating_activity / net_profit

def classify_cfo_quality(
    score: Optional[float],
) -> Optional[str]:
    """
    Classify CFO Quality Score.
    """

    if score is None:
        return None

    if score > 1.0:
        return HIGH_QUALITY

    if score >= 0.5:
        return MODERATE

    return ACCRUAL_RISK

def capex_intensity(
    investing_activity: float,
    sales: float,
) -> Optional[float]:
    """
    Calculate CapEx Intensity.

    Formula:
        abs(Investing Activity) / Sales * 100
    """

    if sales == 0:
        return None

    return (abs(investing_activity) / sales) * 100

def classify_capex_intensity(
    intensity: Optional[float],
) -> Optional[str]:
    """
    Classify CapEx Intensity.
    """

    if intensity is None:
        return None

    if intensity < 3:
        return ASSET_LIGHT

    if intensity <= 8:
        return CAPITAL_MODERATE

    return CAPITAL_INTENSIVE

def fcf_conversion_rate(
    free_cash_flow: float,
    operating_profit: float,
) -> Optional[float]:
    """
    Calculate FCF Conversion Rate.

    Formula:
        Free Cash Flow / Operating Profit * 100
    """

    if operating_profit == 0:
        return None

    return (free_cash_flow / operating_profit) * 100

def classify_fcf_conversion(
    conversion_rate: Optional[float],
) -> Optional[str]:
    """
    Classify FCF Conversion Rate.
    """

    if conversion_rate is None:
        return None

    if conversion_rate > 60:
        return EFFICIENT

    if conversion_rate >= 30:
        return AVERAGE

    return CAPEX_HEAVY

def capital_allocation_pattern(
    operating_activity: float,
    investing_activity: float,
    financing_activity: float,
) -> str:
    """
    Classify the capital allocation pattern based on the signs
    of operating, investing and financing cash flows.
    """

    cfo_positive = operating_activity >= 0
    cfi_positive = investing_activity >= 0
    cff_positive = financing_activity >= 0

    if cfo_positive and not cfi_positive and not cff_positive:
        return REINVESTOR

    if cfo_positive and not cfi_positive and cff_positive:
        return GROWTH_FINANCING

    if cfo_positive and cfi_positive and not cff_positive:
        return SHAREHOLDER_RETURNS

    if cfo_positive and cfi_positive and cff_positive:
        return CASH_ACCUMULATION

    if not cfo_positive and not cfi_positive and not cff_positive:
        return CASH_BURN

    if not cfo_positive and not cfi_positive and cff_positive:
        return DISTRESS

    if not cfo_positive and cfi_positive and not cff_positive:
        return ASSET_LIQUIDATION

    return EXTERNAL_FUNDING
