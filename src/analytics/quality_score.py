"""
Composite Quality Score utilities.
"""

from typing import Optional


def normalize_score(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Normalize a value between 0 and 100.
    """

    if maximum == minimum:
        return 50.0

    score = ((value - minimum) / (maximum - minimum)) * 100

    return round(score, 2)


def composite_quality_score(
    roe: float,
    npm: float,
    debt_to_equity: float,
    interest_coverage: float,
    asset_turnover: float,
) -> float:
    """
    Calculate Composite Quality Score.
    """

    score = (
        roe * 0.30
        + npm * 0.20
        + interest_coverage * 0.20
        + asset_turnover * 0.15
        + (100 - debt_to_equity) * 0.15
    )

    return round(score, 2)