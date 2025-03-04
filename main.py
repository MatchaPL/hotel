import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ใช้ค่าการเชื่อมต่อจาก Environment Variables ของ Railway
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),  # แก้ไขตรงนี้
    "database": os.getenv("MYSQLDATABASE", "railway"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route("/")
def home():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM bookings")
            rooms = cursor.fetchall()
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    room = request.form["room"]
    customer = request.form["customer"]
    channel = request.form["channel"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings
                SET customer=%s, channel=%s, checkin_date=%s, checkout_date=%s, status='booked'
                WHERE room=%s
            """, (customer, channel, checkin, checkout, room))
            conn.commit()
    return redirect(url_for("home"))

@app.route("/cancel/<int:room>")
def cancel_booking(room):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings
                SET customer=NULL, channel=NULL, checkin_date=NULL, checkout_date=NULL, status='available'
                WHERE room=%s
            """, (room,))
            conn.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
