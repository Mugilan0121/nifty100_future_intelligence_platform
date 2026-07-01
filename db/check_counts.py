import sqlite3

conn = sqlite3.connect("nifty100.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT COUNT(*) FROM financial_ratios"
)

count = cursor.fetchone()[0]

print("=" * 40)
print("FINANCIAL_RATIOS ROW COUNT")
print("=" * 40)
print(count)

conn.close()