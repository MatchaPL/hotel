import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ✅ ใช้ค่าการเชื่อมต่อจาก Environment Variables ของ Railway (Private Network)
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),  # ใช้ Private Network
    "port": int(os.getenv("MYSQLPORT", 3306)),  # ใช้ Port 3306 ตามค่าเริ่มต้น
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "railway"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    """ฟังก์ชันเชื่อมต่อ MySQL"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ Database connected successfully!")
        return conn
    except pymysql.MySQLError as e:
        print(f"❌ Database connection failed: {e}")
        return None  # คืนค่า None ถ้าการเชื่อมต่อล้มเหลว

@app.route("/")
def home():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings")
        rooms = cursor.fetchall()
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    """ฟังก์ชันจองห้อง"""
    room = request.form["room"]
    customer = request.form["customer"]
    channel = request.form["channel"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

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
    """ฟังก์ชันยกเลิกการจอง"""
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

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
