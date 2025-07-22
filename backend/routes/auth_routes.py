from flask import Blueprint, jsonify, session
from middleware.auth import check_login

login_bp = Blueprint('login_bp', __name__)

@login_bp.route("/api/login", methods=["POST"])
def login():
    print("[DEBUG] /api/login route hit")
    return check_login()

@login_bp.route("/api/check-auth", methods=["GET"])
def check_auth():
    print("[DEBUG] /api/check-auth route hit")
    if session.get("logged_in"):
        print("[DEBUG] User is authenticated")
        return jsonify({"authenticated": True}), 200
    print("[DEBUG] User is NOT authenticated")
    return jsonify({"authenticated": False}), 401

@login_bp.route("/api/logout", methods=["POST"])
def logout():
    print("[DEBUG] /api/logout route hit")
    session.pop("logged_in", None)
    return jsonify({"message": "Logged out"}), 200
