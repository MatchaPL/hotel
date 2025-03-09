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

# คำนวณราคาห้องพัก
def calculate_price(room_type, nights):
    prices = {
        'Standard': 600,
        'Deluxe': 800,
        'Family': 1200
    }
    return prices.get(room_type, 0) * int(nights)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_bookings")
def get_bookings():
    """Fetch booking data for the dashboard"""
    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT booking_id, room_id, customer_name, phone_number,
                   checkin_date, checkout_date, nights, total_price,
                   payment_status, status, room_type
            FROM bookings
        """)
        bookings = cursor.fetchall()

    for booking in bookings:
        today = datetime.today().date()
        checkin_date = booking['checkin_date']
        checkout_date = booking['checkout_date']

        if today >= checkin_date and today <= checkout_date:
            booking['status'] = 'Checked-In'
        else:
            booking['status'] = 'Checked-Out'

    return jsonify(bookings)

@app.route("/book", methods=["POST"])
def book_room():
    """Book a room"""
    try:
        data = request.form.to_dict()

        # คำนวณราคาห้องพักตามประเภทห้อง
        data["total_price"] = calculate_price(data["room_type"], data["nights"])
        data["booking_id"] = str(uuid.uuid4())

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (room_id, customer_name, phone_number, checkin_date, 
                checkout_date, nights, total_price, status, booking_id, room_type)
                VALUES (%(room_id)s, %(customer_name)s, %(phone_number)s, %(checkin_date)s,
                %(checkout_date)s, %(nights)s, %(total_price)s, 'Checked-In', %(booking_id)s, %(room_type)s)
            """, data)
            conn.commit()

        return jsonify({"message": "Booking successful", "room": data["room_id"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cancel/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    """Cancel a booking"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
        conn.commit()

    return jsonify({"message": "Booking cancelled"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
