import sqlite3

conn = sqlite3.connect("nifty100.db")
cur = conn.cursor()

cur.execute("PRAGMA foreign_key_check;")
violations = cur.fetchall()

print("Foreign Key Violations:", len(violations))

if violations:
    for row in violations:
        print(row)
else:
    print("No foreign key violations found.")

conn.close()