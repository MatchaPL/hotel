from flask import Flask, render_template, request, jsonify
import pymysql
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"

# เชื่อมต่อฐานข้อมูล
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
    """ดึงข้อมูลการจองทั้งหมดมาแสดงบนปฏิทิน"""
    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    with conn.cursor() as cursor:
        cursor.execute("SELECT id, room, customer, checkin_date, checkout_date, booking_status FROM bookings WHERE status='booked'")
        bookings = cursor.fetchall()

    events = []
    for booking in bookings:
        events.append({
            "id": booking["id"],
            "title": f"Room {booking['room']} - {booking['customer']}",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#ff6347" if booking["booking_status"] == "booked" else "#32CD32"
        })
    
    return jsonify(events)

@app.route("/book", methods=["POST"])
def book_room():
    """จองห้อง"""
    try:
        room = request.form.get("room")
        customer = request.form.get("customer")
        phone = request.form.get("phone")
        channel = request.form.get("channel", "")
        checkin = request.form.get("checkin")
        checkout = request.form.get("checkout")
        payment = request.form.get("payment_method")
        room_type = request.form.get("room_type")
        payment_status = request.form.get("payment_status")
        deposit_status = request.form.get("deposit_status")
        payment_date = request.form.get("payment_date")
        received_by = request.form.get("received_by")
        discount = request.form.get("discount", "0")
        booking_status = request.form.get("booking_status")
        staff_name = request.form.get("staff_name")

        # อัปโหลดหลักฐานการชำระเงิน
        payment_proof = request.files.get("payment_proof")
        proof_filename = None
        if payment_proof:
            proof_filename = f"{uuid.uuid4()}_{payment_proof.filename}"
            payment_proof.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))

        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (checkout_date - checkin_date).days

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("SELECT total_price FROM bookings WHERE room = %s", (room,))
            row = cursor.fetchone()
            price_per_night = row["total_price"] if row and row["total_price"] else 0
            total_price = price_per_night * nights

            cursor.execute("""
                INSERT INTO bookings (room, customer, phone_number, channel, checkin_date, checkout_date, 
                    nights, total_price, status, payment_method, booking_id, room_type, payment_status, 
                    deposit_status, payment_date, received_by, discount, booking_status, staff_name, payment_proof)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'booked', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (room, customer, phone, channel, checkin_date, checkout_date, nights, total_price, 
                  payment, str(uuid.uuid4()), room_type, payment_status, deposit_status, payment_date, 
                  received_by, discount, booking_status, staff_name, proof_filename))
            conn.commit()

        return jsonify({"message": "Booking successful", "room": room})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/edit_booking", methods=["POST"])
def edit_booking():
    """แก้ไขการจอง"""
    try:
        booking_id = request.form.get("booking_id")
        customer = request.form.get("customer")
        phone = request.form.get("phone")
        checkin = request.form.get("checkin")
        checkout = request.form.get("checkout")

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE bookings 
                SET customer=%s, phone_number=%s, checkin_date=%s, checkout_date=%s 
                WHERE booking_id=%s
            """, (customer, phone, checkin, checkout, booking_id))
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
        cursor.execute("UPDATE bookings SET status='available', customer=NULL, checkin_date=NULL, checkout_date=NULL WHERE id=%s", (booking_id,))
        conn.commit()
    
    return jsonify({"message": "Booking cancelled", "booking_id": booking_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
