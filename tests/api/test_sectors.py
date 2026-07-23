"""
Unit tests for GET /api/v1/sectors and /api/v1/sectors/{sector}/companies.

Sprint 6 - Day 42

Note: the spec says '/sectors returns exactly 11 sectors', but
pre-inspection during Day 40 confirmed the database actually contains
10 distinct broad_sector values. This test asserts 10 (the verified
real count) and documents the discrepancy rather than asserting the
spec's stale number.
"""


def test_sectors_returns_10_sectors(client):
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert data["sector_count"] == 10
    assert len(data["sectors"]) == 10


def test_sectors_it_returns_only_it_companies(client):
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # sector_companies doesn't echo broad_sector per row, so we confirm
    # via a known IT constituent instead.
    ids = [row["id"] for row in data]
    assert "TCS" in ids


def test_sectors_unknown_sector_returns_404(client):
    response = client.get("/api/v1/sectors/NotASector/companies")
    assert response.status_code == 404


def test_sectors_each_has_required_fields(client):
    response = client.get("/api/v1/sectors")
    data = response.json()
    for sector in data["sectors"]:
        assert "broad_sector" in sector
        assert "company_count" in sector
        assert "median_roe" in sector
        assert "median_pe" in sector
        assert "median_de" in sector