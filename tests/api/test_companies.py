"""
Unit tests for GET /api/v1/companies and /api/v1/companies/{ticker}.

Sprint 6 - Day 42
"""


def test_list_companies_returns_92(client):
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92


def test_list_companies_filter_by_sector(client):
    response = client.get("/api/v1/companies?sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert row["broad_sector"] == "Information Technology"


def test_list_companies_search_partial_name(client):
    response = client.get("/api/v1/companies?search=Tata")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_company_tcs_returns_correct_data(client):
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TCS"
    assert "Tata Consultancy" in data["company_name"]


def test_get_company_invalid_ticker_returns_404(client):
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404


def test_get_company_ticker_case_insensitive(client):
    response = client.get("/api/v1/companies/tcs")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TCS"


def test_get_company_ratios_returns_data(client):
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_company_pl_returns_list(client):
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_company_bs_invalid_ticker_returns_404(client):
    response = client.get("/api/v1/companies/INVALID/bs")
    assert response.status_code == 404