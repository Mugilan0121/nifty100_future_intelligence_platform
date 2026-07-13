"""
Annual Reports Screen

Search a company, see available annual report years with clickable
BSE PDF links. Missing/broken links get a red "unavailable" badge.
"""

import streamlit as st

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports | Nifty 100 Analytics", layout="wide")

st.title("Annual Reports")

companies = get_companies()

if companies.empty:
    st.error("No company data found.")
    st.stop()

companies["display_label"] = companies["id"] + " — " + companies["company_name"]

search_input = st.selectbox(
    "Search by company name or ticker",
    options=companies["display_label"].sort_values(),
    index=None,
    placeholder="Start typing a ticker or company name...",
)

if search_input is None:
    st.info("Select a company to view its annual reports.")
    st.stop()

ticker = search_input.split(" — ")[0].strip()

documents = get_documents(ticker)

if documents.empty:
    st.warning(f"No annual report records found for {ticker}.")
    st.stop()

# ---------------------------------------------------------------------
# Year filter
# ---------------------------------------------------------------------

available_years = sorted(documents["Year"].dropna().unique(), reverse=True)
year_filter = st.multiselect("Filter by year", available_years, default=available_years)

filtered = documents[documents["Year"].isin(year_filter)]

st.subheader(f"{ticker} — Annual Reports")

from utils.db import is_url_valid

with st.spinner("Checking report link availability..."):
    for _, row in filtered.iterrows():
        year = row["Year"]
        url = row.get("Annual_Report")

        col_year, col_link = st.columns([1, 4])
        col_year.write(f"**{year}**")

        if url and isinstance(url, str) and url.strip() and is_url_valid(url):
            col_link.markdown(f"[📄 View Report ({year})]({url})")
        else:
            col_link.markdown(
                "<span style='background-color:#FFC7CE; color:#900; "
                "padding:2px 8px; border-radius:4px;'>Report unavailable</span>",
                unsafe_allow_html=True,
            )