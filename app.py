from flask import Flask, render_template, request, redirect, url_for, session
import uuid
import qrcode
import os
from datetime import datetime
from db import get_db_connection
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "dev-secret-key-change-later"


# -------------------------
# Initialize Database
# -------------------------
# def init_db():
#     conn = sqlite3.connect("data.db")
#     c = conn.cursor()
    
#     # Owners table
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS owners (
#             id TEXT PRIMARY KEY,
#             name TEXT,
#             phone TEXT,
#             vehicle TEXT
#         )
#     """)

#     # Scan logs table
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS scan_logs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             owner_id TEXT,
#             scanned_at TEXT,
#             latitude REAL,
#             longitude REAL
#         )
#     """)
    
#     conn.commit()
#     conn.close()

# init_db()


# -------------------------
# Log scan location API
# -------------------------
@app.route("/log_location", methods=["POST"])
def log_location():
    data = request.get_json()
    print("Location data received:", data)

    owner_id = data.get("owner_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not owner_id:
        return "Invalid", 400

    conn = get_db_connection()
    c = conn.cursor()
    
    map_link = f"https://www.google.com/maps?q={latitude},{longitude}"

    # Update latest scan for this owner
    c.execute("""
        UPDATE scan_logs
        SET latitude=%s, longitude=%s, map_link=%s
        WHERE id = (
            SELECT id FROM scan_logs
            WHERE owner_id=%s
            ORDER BY id DESC
            LIMIT 1
        )
    """, (latitude, longitude, map_link, owner_id))

    conn.commit()
    c.close()
    conn.close()

    return "OK"


# -------------------------
# QR Form Page
# -------------------------
@app.route("/")
def form():
    return render_template("form.html")  # We'll create responsive form.html in templates/


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        vehicle = request.form["vehicle"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        uid = str(uuid.uuid4())

        conn = get_db_connection()
        c = conn.cursor()

        try:
            c.execute("""
                INSERT INTO owners (id, name, phone, vehicle, email, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (uid, name, phone, vehicle, email, password_hash))

            conn.commit()
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"
        finally:
            c.close()
            conn.close()

        return f"""
        <h2>Signup successful!</h2>
        <p>Your QR is ready.</p>
        <a href="/generate">Generate QR</a>
        """

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        c.execute(
            "SELECT id, name, password_hash FROM owners WHERE email=%s",
            (email,)
        )
        user = c.fetchone()

        c.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["owner_id"] = user["id"]
            session["owner_name"] = user["name"]
            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")




# -------------------------# Owner Dashboard
# -------------------------# Temporary Dashboard
@app.route("/dashboard")
def dashboard():
    if "owner_id" not in session:
        return redirect("/login")

    owner_id = session["owner_id"]
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Owner details
    c.execute(
        "SELECT id, name, vehicle, qr_path FROM owners WHERE id=%s",
        (owner_id,)
    )
    owner = c.fetchone()

    # Total scans
    c.execute(
        "SELECT COUNT(*) FROM scan_logs WHERE owner_id=%s",
        (owner_id,)
    )
    total_scans = c.fetchone()[0]

    # Last scan
    c.execute(
        """
        SELECT scanned_at, latitude, longitude, map_link
        FROM scan_logs
        WHERE owner_id=%s
        ORDER BY scanned_at DESC
        LIMIT 1
        """,
        (owner_id,)
    )
    last_scan = c.fetchone()

    # Full scan history
    c.execute(
    """
    SELECT scanned_at, latitude, longitude, map_link
    FROM scan_logs
    WHERE owner_id=%s
    ORDER BY scanned_at DESC
    """,
    (owner_id,)
    )
    scan_history = c.fetchall()



    c.close()
    conn.close()

    return render_template(
        "dashboard.html",
        owner=owner,
        total_scans=total_scans,
        last_scan=last_scan,
        scan_history=scan_history,
    )

## -------------------------#
## QR Generation Endpoint
## -------------------------#

# @app.route("/generate", methods=["POST"])
# def generate_qr(owner_id):
#     # print("GENERATE QR HIT:", owner_id)

#     conn = get_db_connection()
#     c = conn.cursor()

#     # Get owner details
#     c.execute(
#         "SELECT id FROM owners WHERE id = %s",
#         (owner_id,)
#     )
#     owner = c.fetchone()

#     if not owner:
#         return "Owner not found", 404

#     # Generate QR
#     qr_url = f"{request.host_url}q/{owner_id}"
#     qr = qrcode.make(qr_url)

#     if not os.path.exists("static"):
#         os.makedirs("static")

#     qr_path = f"static/{owner_id}.png"
#     qr.save(qr_path)

#     # Save QR path to DB
#     c.execute(
#         "UPDATE owners SET qr_path = %s WHERE id = %s",
#         (qr_path, owner_id)
#     )

#     conn.commit()
#     c.close()
#     conn.close()

#     return redirect("/dashboard")


@app.route("/generate", methods=["POST"])
def generate_qr():
    if "owner_id" not in session:
        print("❌ No owner_id in session")
        return redirect("/login")

    owner_id = session["owner_id"]
    print("✅ Generating QR for:", owner_id)

    qr_url = f"{request.host_url}q/{owner_id}"
    print("QR URL:", qr_url)

    qr = qrcode.make(qr_url)

    if not os.path.exists("static"):
        os.makedirs("static")

    qr_path = f"static/{owner_id}.png"
    qr.save(qr_path)
    print("✅ QR saved at:", qr_path)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE owners SET qr_path=%s WHERE id=%s",
        (qr_path, owner_id)
    )
    conn.commit()
    c.close()
    conn.close()

    print("✅ Database updated")

    return redirect("/dashboard")






# -------------------------
# QR Generation
# -------------------------

# @app.route("/generate/<uid>", methods=["POST"])
# def generate(uid):
#     conn = get_db_connection()
#     c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#     c.execute("SELECT vehicle FROM owners WHERE id=%s", (uid,))
#     owner = c.fetchone()
#     if not owner:
#         return "Invalid owner"

#     qr_url = f"{request.host_url}q/{uid}"
#     qr = qrcode.make(qr_url)

#     os.makedirs("static/qrs", exist_ok=True)
#     qr_path = f"static/qrs/{uid}.png"
#     qr.save(qr_path)

#     c.execute(
#         "UPDATE owners SET qr_path=%s WHERE id=%s",
#         (qr_path, uid)
#     )
#     conn.commit()
#     c.close()
#     conn.close()

#     return redirect(url_for("dashboard", uid=uid))


# -------------------------
# QR Scan Page
# -------------------------
@app.route("/q/<uid>")
def show(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Fetch owner details
    c.execute("SELECT name, phone, vehicle, qr_path FROM owners WHERE id=%s", (uid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Invalid QR"

    # Log scan
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO scan_logs (owner_id, scanned_at) VALUES (%s, %s)",
              (uid, scan_time))
    conn.commit()
    c.close()
    conn.close()

    # -------------------------
    # Responsive Scan Page
    # -------------------------
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vehicle Owner</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center p-4">

  <!-- Card -->
  <div class="bg-white p-6 sm:p-8 rounded-xl shadow-lg w-full max-w-md">
    <h2 class="text-xl sm:text-2xl font-bold mb-2 text-center">{row[0]}</h2>
    <p class="text-gray-600 mb-6 text-center text-sm sm:text-base">Vehicle: {row[2]}</p>

    <a href="tel:{row[1]}"
       class="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg mb-4 sm:mb-6 transition font-medium text-sm sm:text-base">
      📞 Call Owner
    </a>

    <a href="/history/{uid}"
       class="block w-full text-center bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 rounded-lg transition font-medium text-sm sm:text-base">
      📄 View Scan History
    </a>
  </div>

  <script>
    if ("geolocation" in navigator) {{
      navigator.geolocation.getCurrentPosition(
        function(position) {{
          fetch("/log_location", {{
            method: "POST",
            headers: {{
              "Content-Type": "application/json"
            }},
            body: JSON.stringify({{
              owner_id: "{uid}",
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            }})
          }});
        }},
        function(error) {{
          console.log("Location denied");
        }}
      );
    }}
  </script>

</body>
</html>

"""


# -------------------------
# Scan History Page
# -------------------------
@app.route("/history/<uid>")
def history(uid):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("SELECT name, vehicle FROM owners WHERE id=?", (uid,))
    owner = c.fetchone()
    if not owner:
        conn.close()
        return "Invalid QR ID"

    # Fetch scan logs
    c.execute("""
        SELECT scanned_at, latitude, longitude
        FROM scan_logs
        WHERE owner_id=?
        ORDER BY id DESC
    """, (uid,))
    rows = c.fetchall()
    conn.close()

    table_rows = ""
    for r in rows:
        lat = r[1]
        lon = r[2]
        if lat is not None and lon is not None:
            map_link = f'<a href="https://www.google.com/maps?q={lat},{lon}" target="_blank" class="text-blue-600 underline">View Map</a>'
        else:
            map_link = "-"
        table_rows += f"<tr class='border-b'><td class='px-3 py-2'>{r[0]}</td><td class='px-3 py-2'>{lat if lat else '-'}</td><td class='px-3 py-2'>{lon if lon else '-'}</td><td class='px-3 py-2'>{map_link}</td></tr>"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{owner[0]} - Scan History</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen p-4">
  <div class="max-w-4xl mx-auto bg-white p-6 sm:p-8 rounded-xl shadow-lg">
    <h2 class="text-2xl font-bold mb-4">{owner[0]} - {owner[1]} Scan History</h2>
    <p class="mb-4 font-medium">Total Scans: {len(rows)}</p>

    <div class="overflow-x-auto">
      <table class="min-w-full border border-gray-300 divide-y divide-gray-200">
        <thead class="bg-gray-200">
          <tr>
            <th class="px-3 py-2 text-left">Timestamp</th>
            <th class="px-3 py-2 text-left">Latitude</th>
            <th class="px-3 py-2 text-left">Longitude</th>
            <th class="px-3 py-2 text-left">Map Link</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          {table_rows}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""



# -------------------------
# Owner Dashboard (Step 4.2)
# -------------------------
# @app.route("/dashboard/<uid>")
# def dashboard(uid):
#     conn = get_db_connection()
#     c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#     # Owner info
#     c.execute("""
#         SELECT name, phone, vehicle
#         FROM owners
#         WHERE id = %s
#     """, (uid,))
#     owner = c.fetchone()

#     if not owner:
#         c.close()
#         conn.close()
#         return "Invalid dashboard link"

#     # Total scans
#     c.execute("""
#         SELECT COUNT(*) AS total_scans
#         FROM scan_logs
#         WHERE owner_id = %s
#     """, (uid,))
#     total_scans = c.fetchone()["total_scans"]

#     # Last scan time
#     c.execute("""
#         SELECT scanned_at
#         FROM scan_logs
#         WHERE owner_id = %s
#         ORDER BY scanned_at DESC
#         LIMIT 1
#     """, (uid,))
#     last_scan = c.fetchone()
#     last_scan_time = last_scan["scanned_at"] if last_scan else "Never"

#     # Recent scans (last 5)
#     c.execute("""
#         SELECT scanned_at, latitude, longitude
#         FROM scan_logs
#         WHERE owner_id = %s
#         ORDER BY scanned_at DESC
#         LIMIT 5
#     """, (uid,))
#     scans = c.fetchall()

#     c.close()
#     conn.close()

#     # Build scan rows
#     scan_rows = ""
#     for s in scans:
#         if s["latitude"] and s["longitude"]:
#             map_link = f"""
#               <a href="https://www.google.com/maps?q={s['latitude']},{s['longitude']}"
#                  target="_blank"
#                  class="text-blue-600 underline">
#                 View Map
#               </a>
#             """
#         else:
#             map_link = "-"

#         scan_rows += f"""
#         <tr class="border-t">
#           <td class="py-2 text-sm">{s['scanned_at']}</td>
#           <td class="py-2 text-sm text-center">{map_link}</td>
#         </tr>
#         """

#     return f"""
# <!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width, initial-scale=1.0">
#   <title>Owner Dashboard</title>
#   <script src="https://cdn.tailwindcss.com"></script>
# </head>

# <body class="bg-gray-100 min-h-screen p-4">
#   <div class="max-w-3xl mx-auto bg-white rounded-xl shadow-md p-6">

#     <h2 class="text-2xl font-bold mb-1">{owner['name']}</h2>
#     <p class="text-gray-600 mb-4">Vehicle: {owner['vehicle']}</p>

#     <!-- Stats -->
#     <div class="grid grid-cols-2 gap-4 mb-6">
#       <div class="bg-blue-50 p-4 rounded-lg text-center">
#         <p class="text-sm text-gray-600">Total Scans</p>
#         <p class="text-2xl font-bold">{total_scans}</p>
#       </div>

#       <div class="bg-green-50 p-4 rounded-lg text-center">
#         <p class="text-sm text-gray-600">Last Scan</p>
#         <p class="text-sm font-medium">{last_scan_time}</p>
#       </div>
#     </div>

#     <!-- Call button -->
#     <a href="tel:{owner['phone']}"
#        class="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg mb-6 transition">
#       📞 Call Owner
#     </a>

#     <!-- Recent scans -->
#     <h3 class="text-lg font-semibold mb-2">Recent Scans</h3>
#     <table class="w-full text-left">
#       <thead>
#         <tr class="border-b">
#           <th class="py-2 text-sm">Time</th>
#           <th class="py-2 text-sm text-center">Location</th>
#         </tr>
#       </thead>
#       <tbody>
#         {scan_rows if scan_rows else "<tr><td colspan='2' class='py-4 text-center text-gray-500'>No scans yet</td></tr>"}
#       </tbody>
#     </table>

#   </div>
# </body>
# </html>
# """


# -------------------------
# Debug Scans
# -------------------------
@app.route("/debug/scans")
def debug_scans():
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("""
        SELECT owner_id, scanned_at, latitude, longitude
        FROM scan_logs
    """)
    rows = c.fetchall()
    conn.close()

    return "<br>".join([
        f"{r['owner_id']} | {r['scanned_at']} | {r['latitude']} | {r['longitude']}"
        for r in rows
    ])


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
# if __name__ == "__main__":
#     app.run(debug=True)sf