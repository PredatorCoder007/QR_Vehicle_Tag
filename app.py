from flask import Flask, render_template, request
import sqlite3
import uuid
import qrcode
import os
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    #Owners table
    c.execute("""
        CREATE TABLE IF NOT EXISTS owners (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            vehicle TEXT
        )
    """)

    #Scan logs table
    c.execute("""
          CREATE TABLE IF NOT EXISTS scan_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id TEXT,
              scanned_at TEXT
              )
              """)
    
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def form():
    return render_template("form.html")

@app.route("/generate", methods=["POST"])
def generate():
    name = request.form["name"]
    phone = request.form["phone"]
    vehicle = request.form["vehicle"]

    uid = str(uuid.uuid4())


    #save to database
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO owners VALUES (?, ?, ?, ?)",
              (uid, name, phone, vehicle))
    conn.commit()
    conn.close()

    # return f"""
    # <h3>Saved!</h3>
    # <p>Your QR ID: {uid}</p>
    # """
    # --------------------------------
    # QR CODE GENERATION
    # --------------------------------
   
    qr_url = f"{request.host_url}q/{uid}"

    qr = qrcode.make(qr_url)

    # Ensure static folder exists
    if not os.path.exists("static"):
        os.makedirs("static")

    qr_path = f"static/{uid}.png"
    qr.save(qr_path)

    #show QR on browser
    return f"""
    <!DOCTYPE html>
    <html>
<head>
  <title>Your QR</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">

  <div class="bg-white p-6 rounded-xl shadow-md text-center max-w-sm w-full">
    <h2 class="text-xl font-bold mb-4">QR Generated</h2>

    <img src="/static/{uid}.png" class="mx-auto w-64 h-64 mb-4">

    <a href="/static/{uid}.png" download
       class="block bg-green-600 text-white py-2 rounded-lg mb-2">
      Download QR
    </a>

    <p class="text-gray-500 text-sm">
      Stick this QR on your vehicle
    </p>
  </div>

</body>
</html>
"""
  



@app.route("/q/<uid>")
def show(uid):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    #fetch owner details
    c.execute("SELECT name, phone, vehicle FROM owners WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "Invalid QR"
    
    #------------------------------
    # LOG THE SCAN
    #------------------------------
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO scan_logs (owner_id, scanned_at) VALUES (?,?)",
        (uid, scan_time)
    )

    conn.commit()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Vehicle Owner</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center">
      <div class="bg-white p-6 rounded-xl shadow-md text-center max-w-sm w-full">
        <h2 class="text-xl font-bold mb-2">{row[0]}</h2>
        <p class="text-gray-600 mb-4">Vehicle: {row[2]}</p>
        <a href="tel:{row[1]}"
           class="block bg-blue-600 text-white py-3 rounded-lg">
          📞 Call Owner
        </a>
      </div>
    </body>
    </html>
    """

@app.route("/debug/scans")
def debug_scans():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT owner_id, scanned_at FROM scan_logs")
    rows = c.fetchall()
    conn.close()

    return "<br>".join([f"{r[0]} — {r[1]}" for r in rows])


# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

