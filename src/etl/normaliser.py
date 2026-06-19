"""
Normalisation utilities for ETL pipeline.
"""

import re


MONTH_MAP = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}


def normalize_ticker(ticker: str) -> str:
    """Normalize NSE ticker."""

    if ticker is None:
        return ""

    return str(ticker).strip().upper()


def normalize_year(value: str) -> str:
    """Convert year labels into YYYY-MM format."""

    if value is None:
        return "PARSE_ERROR"

    text = str(value).strip()

    if re.match(r"^\d{4}-\d{2}$", text):
        return text

    match = re.match(r"^FY(\d{2})$", text.upper())
    if match:
        year = 2000 + int(match.group(1))
        return f"{year}-03"

    match = re.match(r"^\d{4}$", text)
    if match:
        return f"{text}-03"

    text = text.replace(" ", "-")

    match = re.match(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})$",
        text,
        re.IGNORECASE,
    )
    if match:
        month = MONTH_MAP[match.group(1).upper()]
        year = 2000 + int(match.group(2))
        return f"{year}-{month}"

    match = re.match(
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)-(\d{4})$",
        text,
        re.IGNORECASE,
    )

    if match:
        month = MONTH_MAP[match.group(1)[:3].upper()]
        year = match.group(2)
        return f"{year}-{month}"

    return "PARSE_ERROR"