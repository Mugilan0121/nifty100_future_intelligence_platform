"""
Unit tests for GET /api/v1/health.

Sprint 6 - Day 42
"""


def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_status_ok(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_db_row_counts_present(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert "db_row_counts" in data


def test_health_db_row_counts_has_all_core_tables(client):
    response = client.get("/api/v1/health")
    data = response.json()
    expected_tables = {
        "companies", "sectors", "profitandloss", "balancesheet",
        "cashflow", "financial_ratios", "market_cap", "documents",
        "prosandcons", "peer_groups",
    }
    assert expected_tables.issubset(set(data["db_row_counts"].keys()))


def test_health_uptime_present(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0


def test_health_version_present(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["version"] == "1.0.0"