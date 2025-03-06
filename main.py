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
    """Fetch all bookings for FullCalendar"""
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
            "title": f"{booking['customer']} - {booking['room_type']}",
            "start": booking["checkin_date"].strftime("%Y-%m-%d"),
            "end": booking["checkout_date"].strftime("%Y-%m-%d"),
            "color": "#ff6347",
            "extendedProps": booking
        })
    
    return jsonify(events)

@app.route("/book", methods=["POST"])
def book_room():
    """Book a room"""
    try:
        data = request.form.to_dict()
        data["booking_id"] = str(uuid.uuid4())

        # Assigning default values to missing form fields
        data.setdefault("channel", "Direct")
        data.setdefault("room_type", "Standard")
        data.setdefault("payment_status", "Pending")
        data.setdefault("payment_method", "Cash")
        data.setdefault("deposit_status", "Not Paid")
        data.setdefault("payment_date", None)
        data.setdefault("received_by", "System")
        data.setdefault("discount", "0")
        data.setdefault("booking_status", "Confirmed")
        data.setdefault("staff_name", "Admin")

        payment_proof = request.files.get("payment_proof")
        if payment_proof:
            proof_filename = f"{uuid.uuid4()}_{payment_proof.filename}"
            payment_proof.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))
            data["payment_proof"] = proof_filename
        else:
            data["payment_proof"] = None

        # Calculate number of nights
        checkin_date = datetime.strptime(data["checkin"], "%Y-%m-%d")
        checkout_date = datetime.strptime(data["checkout"], "%Y-%m-%d")
        data["nights"] = (checkout_date - checkin_date).days
        data["total_price"] = data["nights"] * 100  # Assuming $100 per night

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO bookings (room, customer, channel, checkin_date, checkout_date, nights, total_price, status, booking_id, 
                phone_number, room_type, payment_status, payment_method, deposit_status, payment_date, 
                payment_proof, received_by, discount, booking_status, staff_name) 
                VALUES (%(room)s, %(customer)s, %(channel)s, %(checkin)s, %(checkout)s, %(nights)s, %(total_price)s, 
                'booked', %(booking_id)s, %(phone)s, %(room_type)s, %(payment_status)s, %(payment_method)s, 
                %(deposit_status)s, %(payment_date)s, %(payment_proof)s, %(received_by)s, %(discount)s, 
                %(booking_status)s, %(staff_name)s)
            """, data)
            conn.commit()

        return jsonify({"message": "Booking successful", "room": data["room"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    """Cancel a booking"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        conn.commit()

    return jsonify({"message": "Booking cancelled"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
