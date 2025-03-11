from flask import Flask, render_template, request, jsonify
import pymysql
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Database Connection
def get_db_connection():
    try:
        return pymysql.connect(
            host="turntable.proxy.rlwy.net",
            user="root",
            password="jijDgGGBmVEhxmiDyepJBGLxJGWXJTFF",
            database="railway",
            port=24565,
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.MySQLError as e:
        print("Database Connection Error:", e)
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_bookings")
def get_bookings():
    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE status='booked'")
        bookings = cursor.fetchall()

    events = []
    for booking in bookings:
        events.append({
            "id": booking["id"],
            "title": f"{booking['customer']} - Room {booking['room']}",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#4CAF50",
            "extendedProps": booking
        })
    
    return jsonify(events)

@app.route("/get_booking_details/<date>")
def get_booking_details(date):
    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE checkin_date <= %s AND checkout_date >= %s", (date, date))
        bookings = cursor.fetchall()

    return jsonify(bookings)

@app.route("/check_availability", methods=["POST"])
def check_availability():
    """ตรวจสอบห้องว่าง"""
    data = request.form.to_dict()
    room = data.get("room")
    checkin = data.get("checkin")
    checkout = data.get("checkout")

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE room = %s 
            AND (
                (checkin_date <= %s AND checkout_date >= %s)
                OR
                (checkin_date <= %s AND checkout_date >= %s)
            )
        """, (room, checkin, checkin, checkout, checkout))

        existing_booking = cursor.fetchall()

    if existing_booking:
        return jsonify({"available": False, "message": "ห้องนี้ถูกจองแล้วในช่วงเวลาที่เลือก"}), 400

    return jsonify({"available": True, "message": "ห้องนี้ว่าง สามารถจองได้"}), 200

@app.route("/book", methods=["POST"])
def book_room():
    """เพิ่มข้อมูลการจอง"""
    try:
        data = request.form.to_dict()
        data["booking_id"] = str(uuid.uuid4())

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (room, customer, channel, checkin_date, checkout_date, nights, total_price, status, booking_id, 
                phone_number, room_type, payment_status, payment_method, deposit_status, payment_date, 
                payment_proof, received_by, discount, booking_status, staff_name) 
                VALUES (%(room)s, %(customer)s, %(channel)s, %(checkin)s, %(checkout)s, %(nights)s, %(total_price)s, 
                'booked', %(booking_id)s, %(phone)s, %(room_type)s, %(payment_status)s, %(payment)s, 
                %(deposit_status)s, %(payment_date)s, %(payment_proof)s, %(received_by)s, %(discount)s, 
                %(booking_status)s, %(staff_name)s)
            """, data)
            conn.commit()

        return jsonify({"message": "Booking successful", "room": data["room"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
