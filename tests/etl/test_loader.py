"""
Unit tests for src/etl/loader.py.

Sprint 6 - Day 41

Uses synthetic in-memory Excel files (via tmp_path) rather than the
real data/raw files, so these tests stay stable regardless of changes
to the actual dataset and run without requiring the real files to be
present in this environment.
"""

import pandas as pd
import pytest

from src.etl.loader import (
    load_excel,
    load_companies,
    load_profitandloss,
    load_balancesheet,
    load_cashflow,
    CORE_FILES,
)


def _write_core_file(path, columns, rows):
    """
    Write an xlsx with a throwaway metadata row at row 0 and real
    headers at row 1, matching the CORE_FILES header=1 convention.
    """
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([["metadata placeholder"] + [""] * (len(columns) - 1)]).to_excel(
            writer, index=False, header=False, startrow=0
        )
        pd.DataFrame(rows, columns=columns).to_excel(
            writer, index=False, header=True, startrow=1
        )


def _write_plain_file(path, columns, rows):
    """Write a normal xlsx with headers at row 0 (non-core-file convention)."""
    pd.DataFrame(rows, columns=columns).to_excel(path, index=False, header=True)


# --- Row counts ---

def test_load_excel_core_file_row_count(tmp_path):
    path = tmp_path / "profitandloss.xlsx"
    _write_core_file(path, ["company_id", "year", "revenue"], [
        ["TCS", "Mar-23", 1000],
        ["INFY", "Mar-23", 800],
        ["WIPRO", "Mar-23", 500],
    ])
    df = load_excel(path)
    assert len(df) == 3


def test_load_excel_plain_file_row_count(tmp_path):
    path = tmp_path / "sectors.xlsx"
    _write_plain_file(path, ["company_id", "broad_sector"], [
        ["TCS", "Information Technology"],
        ["INFY", "Information Technology"],
    ])
    df = load_excel(path)
    assert len(df) == 2


# --- Column names ---

def test_load_excel_core_file_column_names(tmp_path):
    path = tmp_path / "balancesheet.xlsx"
    _write_core_file(path, ["company_id", "year", "total_assets"], [
        ["TCS", "Mar-23", 5000],
    ])
    df = load_excel(path)
    assert list(df.columns) == ["company_id", "year", "total_assets"]


def test_load_excel_plain_file_column_names(tmp_path):
    path = tmp_path / "market_cap.xlsx"
    _write_plain_file(path, ["company_id", "year", "pe_ratio"], [
        ["TCS", "2023", 30.5],
    ])
    df = load_excel(path)
    assert list(df.columns) == ["company_id", "year", "pe_ratio"]


# --- Header-row selection: core file uses header=1, skipping metadata row ---

def test_core_file_skips_metadata_row(tmp_path):
    path = tmp_path / "cashflow.xlsx"
    _write_core_file(path, ["company_id", "year"], [["TCS", "Mar-23"]])
    df = load_excel(path)
    # If the metadata row leaked in as data, row count would be off or
    # the first column name would be the metadata placeholder text.
    assert "company_id" in df.columns
    assert len(df) == 1


def test_non_core_file_does_not_skip_first_data_row(tmp_path):
    path = tmp_path / "stock_prices.xlsx"
    _write_plain_file(path, ["company_id", "close_price"], [
        ["TCS", 3500.0],
        ["INFY", 1600.0],
    ])
    df = load_excel(path)
    assert len(df) == 2
    assert df.iloc[0]["company_id"] == "TCS"


# --- Normalization side effects ---

def test_company_id_column_normalized(tmp_path):
    path = tmp_path / "prosandcons.xlsx"
    _write_core_file(path, ["company_id", "year"], [["  tcs  ", "Mar-23"]])
    df = load_excel(path)
    assert df.iloc[0]["company_id"] == "TCS"


def test_year_column_normalized(tmp_path):
    path = tmp_path / "analysis.xlsx"
    _write_core_file(path, ["company_id", "year"], [["TCS", "Mar-23"]])
    df = load_excel(path)
    assert df.iloc[0]["year"] == "2023-03"


def test_id_column_normalized_only_for_companies_file(tmp_path):
    path = tmp_path / "companies.xlsx"
    _write_core_file(path, ["id", "company_name"], [["  tcs  ", "Tata Consultancy Services"]])
    df = load_excel(path)
    assert df.iloc[0]["id"] == "TCS"


def test_id_column_not_normalized_for_non_companies_file(tmp_path):
    """
    The 'id' normalization branch only fires when path.name ==
    'companies.xlsx'. A different core file with a plain 'id' column
    (e.g. an autoincrement primary key) should be left untouched.
    """
    path = tmp_path / "documents.xlsx"
    _write_core_file(path, ["id", "company_id"], [[1, "TCS"]])
    df = load_excel(path)
    assert df.iloc[0]["id"] == 1


# --- Named wrapper functions delegate correctly ---

def test_load_companies_wrapper(tmp_path):
    path = tmp_path / "companies.xlsx"
    _write_core_file(path, ["id", "company_name"], [["tcs", "TCS Ltd"]])
    df = load_companies(path)
    assert df.iloc[0]["id"] == "TCS"


def test_load_profitandloss_wrapper(tmp_path):
    path = tmp_path / "profitandloss.xlsx"
    _write_core_file(path, ["company_id", "year"], [["TCS", "Mar-23"]])
    df = load_profitandloss(path)
    assert len(df) == 1


def test_load_balancesheet_wrapper(tmp_path):
    path = tmp_path / "balancesheet.xlsx"
    _write_core_file(path, ["company_id", "year"], [["TCS", "Mar-23"]])
    df = load_balancesheet(path)
    assert len(df) == 1


def test_load_cashflow_wrapper(tmp_path):
    path = tmp_path / "cashflow.xlsx"
    _write_core_file(path, ["company_id", "year"], [["TCS", "Mar-23"]])
    df = load_cashflow(path)
    assert len(df) == 1


# --- CORE_FILES set sanity check ---

def test_core_files_set_contains_expected_files():
    assert "companies.xlsx" in CORE_FILES
    assert "profitandloss.xlsx" in CORE_FILES
    assert "sectors.xlsx" not in CORE_FILES