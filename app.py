from flask import Flask, render_template, request
import sqlite3
import uuid
import qrcode
import os


app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS owners (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            vehicle TEXT
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
    <h2>QR Generated Successfully</h2>
    <p>Scan this QR to contact owner</p>
    <img src= "/{qr_path}" width = "300"><br><br>
    <a href="/{qr_path}" download> Download QR </a>
    """







@app.route("/q/<uid>")
def show(uid):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT name, phone, vehicle FROM owners WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "Invalid QR"

    return f"""
    <h2>{row[0]}</h2>
    <p>Vehicle: {row[2]}</p>
    <a href="tel:{row[1]}">Call Owner</a>
    """

# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

