import sqlite3

conn = sqlite3.connect("nifty100.db")
cur = conn.cursor()

queries = [
    ("Q1", "SELECT COUNT(*) AS company_count FROM companies;"),

    ("Q2", """
    SELECT 'companies' AS table_name, COUNT(*) FROM companies
    UNION ALL
    SELECT 'profitandloss', COUNT(*) FROM profitandloss
    UNION ALL
    SELECT 'balancesheet', COUNT(*) FROM balancesheet
    UNION ALL
    SELECT 'cashflow', COUNT(*) FROM cashflow;
    """),

    ("Q3", """
    SELECT company_id, COUNT(*) AS records
    FROM profitandloss
    GROUP BY company_id
    ORDER BY records DESC
    LIMIT 10;
    """),

    ("Q4", """
    SELECT company_id, COUNT(*) AS records
    FROM profitandloss
    GROUP BY company_id
    ORDER BY records ASC
    LIMIT 10;
    """),

    ("Q5", """
    SELECT MIN(year) AS earliest_year,
           MAX(year) AS latest_year
    FROM profitandloss;
    """),

    ("Q6", """
    SELECT DISTINCT p.company_id
    FROM profitandloss p
    LEFT JOIN companies c
    ON p.company_id = c.id
    WHERE c.id IS NULL;
    """),

    ("Q7", """
    SELECT company_id,
           COUNT(*) AS balance_sheet_records
    FROM balancesheet
    GROUP BY company_id
    ORDER BY balance_sheet_records DESC;
    """),

    ("Q8", """
    SELECT company_id,
           COUNT(*) AS cashflow_records
    FROM cashflow
    GROUP BY company_id
    ORDER BY cashflow_records DESC;
    """),

    ("Q9", """
    SELECT company_id,
           COUNT(*) AS document_count
    FROM documents
    GROUP BY company_id
    ORDER BY document_count DESC
    LIMIT 10;
    """),

    ("Q10", """
    SELECT broad_sector,
           COUNT(*) AS company_count
    FROM sectors
    GROUP BY broad_sector
    ORDER BY company_count DESC;
    """)
]

for name, query in queries:
    try:
        cur.execute(query)
        rows = cur.fetchall()

        print(f"\n{name}: SUCCESS")
        print(f"Rows Returned: {len(rows)}")
        print("Sample:")
        print(rows[:5])
        print("-" * 60)

    except Exception as e:
        print(f"\n{name}: FAILED")
        print(e)
        print("-" * 60)

conn.close()