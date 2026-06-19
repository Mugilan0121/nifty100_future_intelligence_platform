import sqlite3

conn = sqlite3.connect("nifty100.db")

with open("db/schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("Database created successfully")