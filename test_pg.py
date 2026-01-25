import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="qr_vehicle",
    user="qr_user",
    password="#Alex@1997",
)

cur = conn.cursor()
cur.execute("SELECT version();")
db_version = cur.fetchone()
print(f"Connected to database. Version: {db_version}")

cur.close()
conn.close()
