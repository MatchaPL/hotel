import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# ✅ ใช้ค่าจาก Railway Environment Variables
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),  # ✅ ใช้ Private Network
    "port": int(os.getenv("MYSQLPORT", 3306)),  # ✅ ใช้ 3306 ตาม Environment Variables
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "oLkYXKYWsZLVFVzXdKCDhIENAZovNBUx"),
    "database": os.getenv("MYSQLDATABASE", "railway"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    """ฟังก์ชันเชื่อมต่อ MySQL"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        print(f"❌ Database connection failed: {e}")
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/bookings")
def get_bookings():
    """ API ดึงข้อมูลการจองทั้งหมด """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed!"}), 500
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()
    return jsonify(bookings)

@app.route("/book", methods=["POST"])
def book_room():
    """ฟังก์ชันจองห้อง"""
    data = request.json  # รับ JSON request
    room = data.get("room")
    customer = data.get("customer")
    channel = data.get("channel")
    checkin = data.get("checkin")
    checkout = data.get("checkout")
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE bookings
            SET customer=%s, channel=%s, checkin_date=%s, checkout_date=%s, status='booked'
            WHERE room=%s
            """,
            (customer, channel, checkin, checkout, room)
        )
        conn.commit()
    return jsonify({"success": True, "message": "Room booked successfully!"})

@app.route("/cancel/<int:room>", methods=["POST"])
def cancel_booking(room):
    """ฟังก์ชันยกเลิกการจอง"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed!"}), 500
    
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE bookings
            SET customer=NULL, channel=NULL, checkin_date=NULL, checkout_date=NULL, status='available'
            WHERE room=%s
            """,
            (room,)
        )
        conn.commit()
    return jsonify({"success": True, "message": "Booking cancelled!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
