from flask import request, jsonify, session
import os

def check_login():
    print("[DEBUG] Received login request")
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(f"[DEBUG] Provided credentials - Username: {username}, Password: {password}")

    expected_user = os.getenv("LOGIN_USERNAME")
    expected_pass = os.getenv("LOGIN_PASSWORD")
    print(f"[DEBUG] Expected credentials - Username: {expected_user}, Password: {expected_pass}")

    if username == expected_user and password == expected_pass:
        session["logged_in"] = True
        print("[DEBUG] Login successful")
        return jsonify({"message": "Login successful"}), 200
    else:
        print("[DEBUG] Invalid credentials")
        print("[DEBUG] Loaded from env - USER:", os.getenv('LOGIN_USERNAME'), "PASS:", os.getenv('LOGIN_PASSWORD'))

        return jsonify({"error": "Invalid credentials"}), 401
