from src.analytics.quality_score import composite_quality_score


def test_composite_quality_score():

    score = composite_quality_score(
        roe=20,
        npm=15,
        debt_to_equity=30,
        interest_coverage=10,
        asset_turnover=2,
    )

    assert isinstance(score, float)