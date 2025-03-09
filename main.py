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
        conn = pymysql.connect(
            host="turntable.proxy.rlwy.net",
            user="root",
            password="jijDgGGBmVEhxmiDyepJBGLxJGWXJTFF",
            database="railway",
            port=24565,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Database connected successfully!")
        return conn
    except pymysql.MySQLError as e:
        print("❌ Database Connection Error:", e)
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
    """Fetch booking data for the calendar"""
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

    events = []
    for booking in bookings:
        events.append({
            "id": booking["booking_id"],
            "title": f"{booking['customer_name']} ({booking['room_id']})",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#4CAF50" if booking['status'] == 'booked' else "#F44336"
        })

    return jsonify(events)

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
                %(checkout_date)s, %(nights)s, %(total_price)s, 'booked', %(booking_id)s, %(room_type)s)
            """, data)
            conn.commit()

        return jsonify({"message": "Booking successful", "room": data["room_id"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
