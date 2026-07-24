"""
Add SQLite indexes on company_id and year columns for large tables.

Sprint 6 - Day 43

No indexes existed prior to this (confirmed via inspect_db.py).
Indexes target the tables involved in the heaviest per-company lookup
patterns identified in the Day 43 load test (db.screen_companies(),
db._latest_row(), and the various get_statement()/get_ratios() calls).
"""

import sqlite3

conn = sqlite3.connect("nifty100.db")

INDEXES = [
    ("idx_financial_ratios_company_id", "financial_ratios", "company_id"),
    ("idx_financial_ratios_year", "financial_ratios", "year"),
    ("idx_profitandloss_company_id", "profitandloss", "company_id"),
    ("idx_profitandloss_year", "profitandloss", "year"),
    ("idx_balancesheet_company_id", "balancesheet", "company_id"),
    ("idx_balancesheet_year", "balancesheet", "year"),
    ("idx_cashflow_company_id", "cashflow", "company_id"),
    ("idx_cashflow_year", "cashflow", "year"),
    ("idx_market_cap_company_id", "market_cap", "company_id"),
    ("idx_market_cap_year", "market_cap", "year"),
    ("idx_sectors_company_id", "sectors", "company_id"),
    ("idx_documents_company_id", "documents", "company_id"),
    ("idx_prosandcons_company_id", "prosandcons", "company_id"),
    ("idx_peer_groups_company_id", "peer_groups", "company_id"),
    ("idx_peer_percentiles_company_id", "peer_percentiles", "company_id"),
    ("idx_stock_prices_company_id", "stock_prices", "company_id"),
]

for index_name, table, column in INDEXES:
    try:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
        print(f"OK: {index_name} on {table}({column})")
    except sqlite3.Error as e:
        print(f"FAILED: {index_name} on {table}({column}) — {e}")

conn.commit()

print("\nEXISTING INDEXES AFTER RUN:")
for r in conn.execute(
    "SELECT name, tbl_name FROM sqlite_master WHERE type='index'"
).fetchall():
    print(" -", r[0], "on", r[1])

conn.close()