from flask import request, jsonify, session
import os

def check_login():
    print("[DEBUG] Received login request")
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(f"[DEBUG] Provided credentials - Username: {username}, Password: {password}")

    # Check against all LOGIN_USERNAME_X and LOGIN_PASSWORD_X from env
    for i in range(1, 10):  # Supports up to 9 users; extend if needed
        expected_user = os.getenv(f"LOGIN_USERNAME_{i}")
        expected_pass = os.getenv(f"LOGIN_PASSWORD_{i}")

        if expected_user is None or expected_pass is None:
            continue  # Skip if not defined

        print(f"[DEBUG] Checking against - Username: {expected_user}")

        if username == expected_user and password == expected_pass:
            session["logged_in"] = True
            session["user"] = username
            print("[DEBUG] Login successful")
            return jsonify({"message": "Login successful"}), 200

    print("[DEBUG] Invalid credentials for all users")
    return jsonify({"error": "Invalid credentials"}), 401
