from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_dance.contrib.google import google, make_google_blueprint
import google.oauth2.credentials
import google_auth_oauthlib.flow
import os
from flask_dance.consumer.storage.session import SessionStorage

auth_bp = Blueprint('auth', __name__)

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'config/client_secret.json',
    scopes=['https://www.googleapis.com/auth/drive.metadata.readonly',
            'https://www.googleapis.com/auth/calendar.readonly']
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

    # Debugging: Log the OAuth response
    from flask import current_app
    current_app.logger.info("Google OAuth response: %s", google.token)

    resp = google.get("/oauth2/v2/userinfo")
    if not resp or not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return redirect(url_for('auth.home'))

    try:
        user_info = resp.json()
    except ValueError:
        flash("Invalid response from Google.", "danger")
        return redirect(url_for('auth.home'))

    # Save user info in session
    session['user_email'] = user_info.get('email')
    session['user_name'] = user_info.get('name')
    session['user_pic'] = user_info.get('picture')

    flash("Welcome {session['user_name']}!", "success")
    return redirect(url_for('auth.home'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.home'))