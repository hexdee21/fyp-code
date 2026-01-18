from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
import jwt
import datetime
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Secret key for JWT signing
SECRET_KEY = "b@@zig@RkEthAyHaIn"

# MySQL connection config
db_config = {
    "host": "127.0.0.1",
    "user": "admin",
    "password": "admin123",
    "database": "aml_system"
}

# ==============================================================
# 🟢 REGISTER NEW USER
# ==============================================================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        passport = data.get("passport_number")
        role = "user"  # always normal user

        if not email or not password or not passport:
            return jsonify({"success": False, "message": "Missing fields"}), 400

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        # Check if email exists
        cur.execute("SELECT email FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"success": False, "message": "User already exists"}), 409

        # Create wallet
        wallet = f"WLT-{random.randint(1000, 9999)}"

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Insert user
        cur.execute(
            """
            INSERT INTO users (email, passport_number, password_hash, role, wallet_address)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (email, passport, hashed_pw, role, wallet)
        )
        conn.commit()

        # Create wallet entry with 1000 PKR
        cur.execute(
            """
            INSERT INTO wallets (wallet_id, user_email, balance)
            VALUES (%s, %s, %s)
            """,
            (wallet, email, 1000.00)
        )
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "wallet": wallet
        }), 201

    except Exception as e:
        print("[REGISTER ERROR]", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# ==============================================================
# 🟠 LOGIN USER
# ==============================================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Missing credentials"}), 400

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": "User not found"}), 401

        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"success": False, "message": "Invalid password"}), 401

        # Create JWT
        token = jwt.encode(
            {
                "email": user["email"],
                "role": user["role"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "role": user["role"],
            "wallet": user.get("wallet_address")
        }), 200

    except Exception as e:
        print("[LOGIN ERROR]", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# ==============================================================
# 🟡 GET WALLET BALANCE
# ==============================================================
@app.route("/wallet/balance", methods=["GET"])
def get_balance():
    try:
        wallet_id = request.headers.get("X-Wallet-ID")
        if not wallet_id:
            return jsonify({"success": False, "message": "Missing wallet header"}), 400

        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT balance FROM wallets WHERE wallet_id = %s", (wallet_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return jsonify({"success": False, "message": "Wallet not found"}), 404

        return jsonify({"success": True, "balance": float(row["balance"])}), 200

    except Exception as e:
        print("[BALANCE ERROR]", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# ==============================================================
# 🔴 ADMIN DEPOSIT MONEY
# ==============================================================
@app.route("/admin/deposit", methods=["POST"])
def admin_deposit():
    try:
        data = request.get_json()
        wallet_id = data.get("wallet_id")
        amount = float(data.get("amount", 0))

        if not wallet_id or amount <= 0:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        # Read token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "message": "Missing token"}), 401

        # Decode token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            return jsonify({"success": False, "message": "Invalid token"}), 401

        # Must be admin
        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Not authorized"}), 403

        # Update balance
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()

        cur.execute(
            "UPDATE wallets SET balance = balance + %s WHERE wallet_id = %s",
            (amount, wallet_id)
        )
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"success": True, "message": f"Deposited {amount} PKR to {wallet_id}"}), 200

    except Exception as e:
        print("[DEPOSIT ERROR]", e)
        return jsonify({"success": False, "message": "Server error"}), 500



# ==============================================================
# RUN SERVER
# ==============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
