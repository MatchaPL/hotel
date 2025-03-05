from flask import Flask, render_template, request, jsonify
import pymysql
from datetime import datetime
import uuid

app = Flask(__name__)

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
    """โหลดข้อมูลห้องพัก"""
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed!", 500

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings")
        rooms = cursor.fetchall()
    
    return render_template("index.html", rooms=rooms)

@app.route("/book", methods=["POST"])
def book_room():
    """จองห้อง"""
    try:
        room = request.form["room"]
        customer = request.form["customer"]
        phone = request.form["phone"]
        channel = request.form["channel"]
        checkin = request.form["checkin"]
        checkout = request.form["checkout"]
        payment = request.form["payment"]

        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (checkout_date - checkin_date).days

        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection failed!"}), 500

        with conn.cursor() as cursor:
            cursor.execute("SELECT total_price FROM bookings WHERE room = %s", (room,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"message": "Room not found"}), 404

            price_per_night = row["total_price"]
            total_price = price_per_night * nights

            cursor.execute("""
                UPDATE bookings
                SET customer=%s, phone_number=%s, channel=%s, checkin_date=%s, checkout_date=%s, 
                    nights=%s, total_price=%s, status='booked', payment_method=%s, booking_id=%s
                WHERE room=%s
            """, (customer, phone, channel, checkin, checkout, nights, total_price, payment, str(uuid.uuid4()), room))
            conn.commit()

        return jsonify({"message": "Booking successful", "room": room})

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except ValueError:
        return jsonify({"message": "Invalid date format"}), 400

@app.route("/cancel/<room>", methods=["POST"])
def cancel_booking(room):
    """ยกเลิกการจอง"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection failed!"}), 500

    with conn.cursor() as cursor:
        cursor.execute("UPDATE bookings SET status='available', customer=NULL, checkin_date=NULL, checkout_date=NULL WHERE room = %s", (room,))
        conn.commit()
    
    return jsonify({"message": "Booking cancelled", "room": room})

if __name__ == "__main__":
    app.run(debug=True)
