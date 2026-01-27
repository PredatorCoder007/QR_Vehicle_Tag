from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT current_database();")
print(cur.fetchone())
cur.close()
conn.close()
