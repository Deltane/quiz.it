from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_dance.contrib.google import google
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return render_template('base.html')

@auth_bp.route('/login')
def login():
    if session.get("user_email"):
        return redirect(url_for("main.home"))
    return redirect(url_for('google.login'))

@auth_bp.route("/google-callback")
def google_callback():
    print("Authorized route hit")
    print("Is Google authorized:", google.authorized)

    if not google.authorized:
        flash("Not authorized with Google", "danger")
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    print("Google response status:", resp.status_code)

    if not resp.ok:
        flash("Failed to fetch user info from Google", "danger")
        print("Google response error:", resp.text)
        return redirect(url_for("main.home"))

    user_info = resp.json()
    print("User info:", user_info)

    # Save user info in session
    session["user_email"] = user_info["email"]
    session["user_name"] = user_info["name"]
    session["user_pic"] = user_info["picture"]

    print("User email stored in session:", session.get("user_email"))

    flash(f"Welcome, {user_info['email']}!", "success")
    return redirect(url_for("auth.home"))

# Error handling for invalid OAuth requests
@auth_bp.errorhandler(400)
def handle_invalid_oauth_request(error):
    flash("Invalid OAuth request", "danger")
    return redirect(url_for("main.home"))

# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         # Handle registration form (stub)
#         pass
#     return render_template('register.html')
