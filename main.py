from flask import Flask, render_template, request, jsonify
import pymysql
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# เชื่อมต่อฐานข้อมูล Railway
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
    """ดึงข้อมูลการจองทั้งหมด"""
    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    with conn.cursor() as cursor:
        cursor.execute("SELECT id, room, customer, checkin_date, checkout_date FROM bookings WHERE status='booked'")
        bookings = cursor.fetchall()

    events = []
    for booking in bookings:
        events.append({
            "id": booking["id"],
            "title": f"Room {booking['room']} - {booking['customer']}",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#ff6347"
        })
    
    return jsonify(events)

@app.route("/book", methods=["POST"])
def book_room():
    """เพิ่มการจองใหม่"""
    try:
        room = request.form.get("room")
        customer = request.form.get("customer")
        phone = request.form.get("phone")
        checkin = request.form.get("checkin")
        checkout = request.form.get("checkout")

        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (room, customer, phone_number, checkin_date, checkout_date, status)
                VALUES (%s, %s, %s, %s, %s, 'booked')
            """, (room, customer, phone, checkin_date, checkout_date))
            conn.commit()

        return jsonify({"message": "Booking successful"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/update_booking", methods=["POST"])
def update_booking():
    """อัปเดตวันจองเมื่อมีการลาก Event"""
    try:
        booking_id = request.form.get("id")
        new_checkin = request.form.get("start")
        new_checkout = request.form.get("end")

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings SET checkin_date=%s, checkout_date=%s WHERE id=%s
            """, (new_checkin, new_checkout, booking_id))
            conn.commit()

        return jsonify({"message": "Booking updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    """ยกเลิกการจอง"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("UPDATE bookings SET status='available' WHERE id=%s", (booking_id,))
        conn.commit()
    
    return jsonify({"message": "Booking cancelled"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
