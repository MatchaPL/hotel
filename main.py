import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ใช้ค่าการเชื่อมต่อจาก Environment Variables ของ Railway
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),  # ใช้ค่าจาก Railway
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "railway"),
    "port": int(os.getenv("MYSQLPORT", 3306)),  # ต้องระบุ port ด้วย
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"⚠️ Database Connection Error: {e}")
        return None

@app.route("/")
def home():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings")
        rooms = cursor.fetchall()
    conn.close()
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500
    room = request.form["room"]
    customer = request.form["customer"]
    channel = request.form["channel"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE bookings
            SET customer=%s, channel=%s, checkin_date=%s, checkout_date=%s, status='booked'
            WHERE room=%s
        """, (customer, channel, checkin, checkout, room))
        conn.commit()
    conn.close()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
