from flask import Blueprint, redirect, url_for, session, current_app, request
from app import oauth  # Import the oauth object
import os
import logging
import uuid
from flask_login import login_user, logout_user, current_user
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

def init_oauth(oauth):
    google_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    
    if not google_client_id or not google_client_secret:
        current_app.logger.error("GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET environment variable not set")
        raise ValueError("GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET environment variable not set")
    
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

@auth_bp.route('/login')
def login():
    try:
        redirect_uri = url_for('auth.authorize', _external=True)
        nonce = str(uuid.uuid4())  # Generate a unique nonce
        state = str(uuid.uuid4())  # Generate a unique state
        session['oauth_nonce'] = nonce  # Store the nonce in the session
        session['oauth_state'] = state  # Store the state in the session
        current_app.logger.info(f"Redirect URI: {redirect_uri}, Nonce: {nonce}, State: {state}")
        return oauth.google.authorize_redirect(redirect_uri, nonce=nonce, state=state)
    except Exception as e:
        current_app.logger.error(f"Error in /auth/login: {e}")
        return "An error occurred during login. Check server logs for details.", 500

@auth_bp.route('/authorize')
def authorize():
    try:
        current_app.logger.info("Starting authorization process.")  # Log statement for debugging
        token = oauth.google.authorize_access_token()
        nonce = session.pop('oauth_nonce', None)  # Retrieve and remove the nonce from the session
        state = session.pop('oauth_state', None)  # Retrieve and remove the state from the session
        if not nonce or not state:
            raise ValueError("Missing nonce or state in session")

        # Validate the ID token with the nonce
        user_info = oauth.google.parse_id_token(token, nonce=nonce) or {}
        userinfo_response = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info.update(userinfo_response.json() or {})
        from app.models import User, db  # Import inside to avoid circular import
        user = User.query.filter_by(email=user_info["email"]).first()
        if not user:
            user = User(email=user_info["email"], username=user_info.get("name", user_info["email"]))
            db.session.add(user)
            db.session.commit()
        session['user_email'] = user_info['email']
        session['user_name'] = user_info.get('name', user_info['email'])
        session['user_pic'] = user_info.get('picture', '')

        # Check if user exists in the database
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            # Create a new user if not exists
            current_app.logger.info(f"Creating new user with email: {user_info['email']}")  # Log statement for debugging
            if user_info.get('password_hash') is None:
                user_info['password_hash'] = 'default_hash'  # Set a default password hash
            user = User(username=user_info.get('name', user_info['email']), email=user_info['email'], password_hash=user_info['password_hash'])
            db.session.add(user)
            db.session.commit()

        # Log the user in
        login_user(user)

        current_app.logger.info(f"User {session['user_email']} logged in successfully.")
        return redirect(url_for('dashboard.dashboard_view'))
    except Exception as e:
        current_app.logger.error(f"Error in /auth/authorize: {e}")
        return "An error occurred during authorization. Check server logs for details.", 500

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    current_app.logger.info("User logged out and session cleared.")
    return redirect(url_for('quiz_routes.home'))
