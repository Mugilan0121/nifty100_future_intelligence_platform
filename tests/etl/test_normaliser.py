import pytest

from src.etl.normaliser import normalize_year
from src.etl.normaliser import normalize_ticker


def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"


def test_year_fy24():
    assert normalize_year("FY24") == "2024-03"


def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"


def test_year_2023():
    assert normalize_year("2023") == "2023-03"


def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"


def test_year_garbage():
    assert normalize_year("xyz") == "PARSE_ERROR"


def test_ticker_strip():
    assert normalize_ticker(" TCS ") == "TCS"


def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_hyphen():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"


def test_ticker_ampersand():
    assert normalize_ticker("m&m") == "M&M"

def test_year_mar_space():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_march_2023():
    assert normalize_year("March-2023") == "2023-03"

def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"

def test_year_fy23():
    assert normalize_year("FY23") == "2023-03"

def test_year_fy25():
    assert normalize_year("FY25") == "2025-03"

def test_year_jan24():
    assert normalize_year("Jan-24") == "2024-01"

def test_year_feb24():
    assert normalize_year("Feb-24") == "2024-02"

def test_year_apr24():
    assert normalize_year("Apr-24") == "2024-04"

def test_year_may24():
    assert normalize_year("May-24") == "2024-05"

def test_year_null():
    assert normalize_year(None) == "PARSE_ERROR"

def test_ticker_infy():
    assert normalize_ticker("infy") == "INFY"

def test_ticker_reliance():
    assert normalize_ticker("reliance") == "RELIANCE"

def test_ticker_hdfc():
    assert normalize_ticker("hdfc") == "HDFC"

def test_ticker_upper():
    assert normalize_ticker("TCS") == "TCS"

def test_ticker_spaces_both():
    assert normalize_ticker("  infy  ") == "INFY"

def test_ticker_empty():
    assert normalize_ticker("") == ""

def test_ticker_none():
    assert normalize_ticker(None) == ""

def test_ticker_numbers():
    assert normalize_ticker("abc123") == "ABC123"

def test_ticker_special():
    assert normalize_ticker("ltimindtree") == "LTIMINDTREE"

def test_ticker_mixed():
    assert normalize_ticker("InFy") == "INFY"

def test_year_oct24():
    assert normalize_year("Oct-24") == "2024-10"

def test_year_nov24():
    assert normalize_year("Nov-24") == "2024-11"

def test_year_dec24():
    assert normalize_year("Dec-24") == "2024-12"

def test_year_invalid_month():
    assert normalize_year("Abc-24") == "PARSE_ERROR"

def test_year_empty():
    assert normalize_year("") == "PARSE_ERROR"

def test_ticker_wipro():
    assert normalize_ticker("wipro") == "WIPRO"

def test_ticker_titan():
    assert normalize_ticker("titan") == "TITAN"

def test_ticker_nested_spaces():
    assert normalize_ticker("   tcs   ") == "TCS"

def test_ticker_bajaj():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

def test_ticker_mixed_case():
    assert normalize_ticker("ReLiAnCe") == "RELIANCE"