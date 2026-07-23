"""
Unit tests for GET /api/v1/screener.

Sprint 6 - Day 42
"""


def test_screener_min_roe_returns_only_qualifying_companies(client):
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    for row in data["results"]:
        assert row["roe_pct"] is not None
        assert row["roe_pct"] >= 15


def test_screener_no_filters_returns_all_companies(client):
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0


def test_screener_sector_filter(client):
    response = client.get("/api/v1/screener?sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    for row in data["results"]:
        assert row["broad_sector"] == "Information Technology"


def test_screener_max_de_filter(client):
    response = client.get("/api/v1/screener?max_de=0.5")
    assert response.status_code == 200
    data = response.json()
    for row in data["results"]:
        assert row["debt_to_equity"] is not None
        assert row["debt_to_equity"] <= 0.5


def test_screener_invalid_negative_max_de_returns_400(client):
    response = client.get("/api/v1/screener?max_de=-10")
    assert response.status_code == 400


def test_screener_invalid_roe_out_of_range_returns_400(client):
    response = client.get("/api/v1/screener?min_roe=99999")
    assert response.status_code == 400