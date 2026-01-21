import sqlite3

conn = sqlite3.connect("data.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE scan_logs ADD COLUMN latitude REAL")
    print("latitude column added")
except:
    print("latitude column already exists")

try:
    c.execute("ALTER TABLE scan_logs ADD COLUMN longitude REAL")
    print("longitude column added")
except:
    print("longitude column already exists")

conn.commit()
conn.close()

print("Migration completed")
