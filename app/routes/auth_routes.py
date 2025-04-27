from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
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
        return redirect(url_for("auth.home"))
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
        return redirect(url_for("auth.home"))

    user_info = resp.json()
    print("User info:", user_info)

    # Save user info in session
    session["user_email"] = user_info["email"]
    session["user_name"] = user_info["name"]
    session["user_pic"] = user_info["picture"]

    print("User email stored in session:", session.get("user_email"))

    flash(f"Welcome, {user_info['email']}!", "success")
    
    response = make_response(redirect(url_for("auth.home")))
    allowed_origins = ["https://trusted-domain.com", "https://another-trusted-domain.com"]
    origin = request.headers.get("Origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    return response

# Error handling for invalid OAuth requests
@auth_bp.errorhandler(400)
def handle_invalid_oauth_request(error):
    flash("Invalid OAuth request", "danger")
    return redirect(url_for("auth.home"))

# Add log out for testing
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.home'))
