import pymysql
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "caboose.proxy.rlwy.net"),
    "port": int(os.getenv("MYSQLPORT", 41067)),  # ใช้ค่าจาก Environment
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", "oLkYXKYWsZLVFVzXdKCDhIENAZovNBUx"),
    "database": os.getenv("MYSQLDATABASE", "railway"),
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
