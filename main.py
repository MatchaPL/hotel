import pymysql
import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# ✅ ใช้ค่าจาก Railway Environment Variables
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),
    "port": int(os.getenv("MYSQLPORT", 3306)),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "jijDgGGBmVEhxmiDyepJBGLxJGWXJTFF"),
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
        return None

@app.route("/")
def home():
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT room, room_type, total_price, status, customer, checkin_date, checkout_date 
            FROM bookings
        """)
        rooms = cursor.fetchall()
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    """ฟังก์ชันจองห้อง"""
    room = request.form["room"]
    customer = request.form["customer"]
    phone = request.form["phone"]
    channel = request.form["channel"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]
    payment = request.form["payment"]
    
    # คำนวณจำนวนคืนที่เข้าพัก
    nights = (pymysql.Date(checkout) - pymysql.Date(checkin)).days

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500 

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT total_price FROM bookings WHERE room = %s
        """, (room,))
        price_per_night = cursor.fetchone()["total_price"]
        total_price = price_per_night * nights

        cursor.execute("""
            UPDATE bookings
            SET customer=%s, phone_number=%s, channel=%s, checkin_date=%s, checkout_date=%s, 
                nights=%s, total_price=%s, status='booked', payment_method=%s, booking_id=%s
            WHERE room=%s
        """, (customer, phone, channel, checkin, checkout, nights, total_price, payment, str(uuid.uuid4()), room))
        conn.commit()
    
    return jsonify({"message": "Booking successful", "room": room})

@app.route("/cancel/<int:room>", methods=["POST"])
def cancel_booking(room):
    """ฟังก์ชันยกเลิกการจอง"""
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE bookings
            SET customer=NULL, phone_number=NULL, channel=NULL, checkin_date=NULL, checkout_date=NULL, 
                nights=NULL, total_price=NULL, status='available', payment_method=NULL, booking_id=NULL
            WHERE room=%s
        """, (room,))
        conn.commit()

    return jsonify({"message": "Booking canceled", "room": room})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
