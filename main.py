import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ✅ ใช้ค่าการเชื่อมต่อ MySQL จาก Railway
DB_CONFIG = {
    "host": "caboose.proxy.rlwy.net",  # ใช้ค่าจาก Railway
    "port": 41607,  # ใส่ค่าจาก Railway (เปลี่ยนตามของคุณ)
    "user": "root",
    "password": "oLkYXKYWsZLVFVzXdKCDhIENAZovNBUx",  # ใช้ค่าจริงจาก Railway
    "database": "railway",
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
