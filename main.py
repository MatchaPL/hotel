import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ✅ ใช้ค่าจาก Railway Environment Variables
DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "mysql.railway.internal"),
    "port": int(os.getenv("MYSQLPORT", 3306)),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "oLkYXKYWsZLVFVzXdKCDhIENAZovNBUx"),
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
        cursor.execute("SELECT * FROM bookings")
        rooms = cursor.fetchall()
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    """ฟังก์ชันจองห้อง"""
    room = request.form["room"]
    customer = request.form["customer"]
    phone_number = request.form["phone_number"]
    channel = request.form["channel"]
    checkin = request.form["checkin"]
    checkout = request.form["checkout"]
    room_type = request.form["room_type"]
    nights = request.form["nights"]
    total_price = request.form["total_price"]
    payment_status = request.form["payment_status"]
    payment_method = request.form["payment_method"]
    deposit_status = request.form["deposit_status"]
    payment_date = request.form["payment_date"]
    payment_proof = request.form["payment_proof"]
    received_by = request.form["received_by"]
    discount = request.form["discount"]
    booking_id = request.form["booking_id"]
    booking_status = request.form["booking_status"]
    staff_name = request.form["staff_name"]
    staff_notes = request.form["staff_notes"]

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE bookings
            SET customer=%s, phone_number=%s, channel=%s, checkin_date=%s, checkout_date=%s,
                room_type=%s, nights=%s, total_price=%s, payment_status=%s, payment_method=%s,
                deposit_status=%s, payment_date=%s, payment_proof=%s, received_by=%s, 
                discount=%s, booking_id=%s, booking_status=%s, staff_name=%s, staff_notes=%s, status='booked'
            WHERE room=%s
        """, (customer, phone_number, channel, checkin, checkout, room_type, nights, total_price,
              payment_status, payment_method, deposit_status, payment_date, payment_proof,
              received_by, discount, booking_id, booking_status, staff_name, staff_notes, room))
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
            SET customer=NULL, phone_number=NULL, channel=NULL, checkin_date=NULL, checkout_date=NULL,
                room_type=NULL, nights=NULL, total_price=NULL, payment_status=NULL, payment_method=NULL,
                deposit_status=NULL, payment_date=NULL, payment_proof=NULL, received_by=NULL, 
                discount=NULL, booking_id=NULL, booking_status=NULL, staff_name=NULL, staff_notes=NULL, status='available'
            WHERE room=%s
        """, (room,))
        conn.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
