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
        cursor.execute("""
            SELECT b.booking_id, r.room_number, b.customer_name, b.checkin_date, b.checkout_date 
            FROM bookings b 
            JOIN rooms r ON b.room_id = r.room_id 
            WHERE b.status='Booked'
        """)
        bookings = cursor.fetchall()

    events = []
    for booking in bookings:
        events.append({
            "id": booking["booking_id"],
            "title": f"{booking['customer_name']} - Room {booking['room_number']}",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#28a745",
            "extendedProps": booking
        })
    
    return jsonify(events)

@app.route("/book", methods=["POST"])
def book_room():
    try:
        data = request.form.to_dict()

        # Generate unique booking_id
        data["booking_id"] = str(uuid.uuid4())
        data["status"] = 'Booked'

        # Convert room_id and numeric data
        data["room_id"] = int(data.get("room", 0))
        data["nights"] = int(data.get("nights", 1))
        data["total_price"] = float(data.get("total_price", 0.0))

        # Handle payment proof
        payment_proof = request.files.get("payment_proof")
        if payment_proof:
            proof_filename = f"{uuid.uuid4()}_{payment_proof.filename}"
            payment_proof.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))
            data["payment_proof"] = proof_filename
        else:
            data["payment_proof"] = None

        # Database Connection
        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (booking_id, room_id, customer_name, phone_number, 
                checkin_date, checkout_date, nights, total_price, payment_status, 
                payment_proof, status) 
                VALUES (%(booking_id)s, %(room_id)s, %(customer)s, %(phone)s, %(checkin)s, 
                %(checkout)s, %(nights)s, %(total_price)s, %(payment_status)s, 
                %(payment_proof)s, 'Booked')
            """, data)
            conn.commit()

        return jsonify({"message": "Booking successful", "room": data["room_id"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cancel/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("UPDATE bookings SET status='Cancelled' WHERE booking_id = %s", (booking_id,))
        conn.commit()

    return jsonify({"message": "Booking cancelled"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
