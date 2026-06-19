import sqlite3

conn = sqlite3.connect("nifty100.db")

tables = conn.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""").fetchall()

for table in tables:
    print(table[0])

conn.close()