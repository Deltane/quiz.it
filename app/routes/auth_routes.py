from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_dance.contrib.google import google
from flask_dance.contrib.google import make_google_blueprint
import os

auth_bp = Blueprint('auth', __name__)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"],
    redirect_to="auth.google_callback"
)

@auth_bp.route('/')
def home():
    return render_template('base.html')

@auth_bp.route('/login')
def login():
    if session.get("user_email"):
        return redirect(url_for('auth.home'))
    return redirect(url_for('google.login'))

@auth_bp.route('/login/google/authorized')
def google_callback():
    if not google.authorized:
        flash("Authorization failed. Please try again.", "danger")
        return redirect(url_for('auth.home'))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return redirect(url_for('auth.home'))

    user_info = resp.json()

    # Save user info in session
    session['user_email'] = user_info.get('email')
    session['user_name'] = user_info.get('name')
    session['user_pic'] = user_info.get('picture')

    flash(f"Welcome {session['user_name']}!", "success")
    return redirect(url_for('auth.home'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.home'))
