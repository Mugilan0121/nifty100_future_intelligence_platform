import sqlite3

conn = sqlite3.connect("nifty100.db")

conn.execute("PRAGMA foreign_keys = ON")

status = conn.execute(
    "PRAGMA foreign_keys"
).fetchone()

print("Foreign Keys Enabled:", status[0])

conn.close()