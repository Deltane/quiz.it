from flask import Blueprint, redirect, url_for, session, current_app, request, jsonify
from flask_login import login_user, logout_user, current_user
from app import oauth, db
from app.models import User
import os
import uuid

auth_bp = Blueprint('auth', __name__)

def init_oauth(oauth):
    google_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    if not google_client_id or not google_client_secret:
        current_app.logger.error("Missing Google OAuth credentials")
        raise ValueError("Google OAuth credentials not set")

    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={'scope': 'openid email profile'}
    )

@auth_bp.route('/login')
def login():
    try:
        redirect_uri = url_for('auth.authorize', _external=True)
        nonce = str(uuid.uuid4())
        state = str(uuid.uuid4())
        session['oauth_nonce'] = nonce
        session['oauth_state'] = state
        
        # If we have a shared_quiz_id in the session, preserve it
        if 'shared_quiz_id' in session:
            current_app.logger.info(f"Preserving shared_quiz_id: {session['shared_quiz_id']}")
        
        return oauth.google.authorize_redirect(redirect_uri, nonce=nonce, state=state)
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return "Login failed.", 500

@auth_bp.route('/authorize')
def authorize():
    try:
        token = oauth.google.authorize_access_token()
        nonce = session.pop('oauth_nonce', None)
        state = session.pop('oauth_state', None)
        if not nonce or not state:
            raise ValueError("Missing nonce or state")

        user_info = oauth.google.parse_id_token(token, nonce=nonce) or {}
        userinfo_response = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info.update(userinfo_response.json() or {})

        email = user_info.get("email")
        name = user_info.get("name", email)
        picture = user_info.get("picture", "") # Get picture from user_info

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                username=name,
                email=email,
                password_hash='google-oauth',
                picture=picture  # Save picture URL to the User model
            )
            db.session.add(user)
        else:
            # Update picture if it has changed or was not set before
            if user.picture != picture:
                user.picture = picture
        
        db.session.commit() # Commit changes for new or existing user

        login_user(user)
        session['user_id'] = user.id
        session['user_email'] = email
        session['user_name'] = name
        session['user_pic'] = picture
        
        # Check for any pending quiz shares for this email
        from app.models import PendingQuizShare, QuizShare
        pending_shares = PendingQuizShare.query.filter_by(recipient_email=email).all()
        
        # Convert pending shares to actual shares
        for pending in pending_shares:
            # Create a new QuizShare entry
            new_share = QuizShare(
                quiz_id=pending.quiz_id,
                shared_with_user_id=user.id,
                shared_by_user_id=pending.shared_by_user_id
            )
            db.session.add(new_share)
            db.session.delete(pending)  # Remove the pending share
        
        db.session.commit()

        # Check if there's a shared quiz to handle after login
        shared_quiz_id = session.get('shared_quiz_id')
        if shared_quiz_id:
            current_app.logger.info(f"Redirecting to shared quiz: {shared_quiz_id}")
            
            # Get the quiz and check if it's shared with this user
            quiz = Quiz.query.get(shared_quiz_id)
            if not quiz:
                flash("The requested quiz could not be found.", "error")
                return redirect(url_for('dashboard.dashboard_view'))
                
            # Check if the user is the quiz owner
            if quiz.user_id == user.id:
                return redirect(url_for('quiz_routes.redo_quiz', quiz_id=shared_quiz_id))
                
            # Check if quiz is shared with this user through QuizShare
            quiz_share = QuizShare.query.filter_by(
                quiz_id=shared_quiz_id,
                shared_with_user_id=user.id
            ).first()
            
            # Check for pending share
            if not quiz_share:
                pending_share = PendingQuizShare.query.filter_by(
                    quiz_id=shared_quiz_id,
                    recipient_email=user.email
                ).first()
                
                if pending_share:
                    # Convert pending share to actual share
                    quiz_share = QuizShare(
                        quiz_id=shared_quiz_id,
                        shared_with_user_id=user.id,
                        shared_by_user_id=pending_share.shared_by_user_id
                    )
                    db.session.add(quiz_share)
                    db.session.delete(pending_share)
                    db.session.commit()
            
            if quiz_share:
                # Set session variables to show the shared quiz modal on dashboard
                session['show_shared_quiz_modal'] = True
                session['shared_quiz_id'] = shared_quiz_id
                session['shared_quiz_sender_id'] = quiz_share.shared_by_user_id
                
                # Redirect to dashboard with the modal setup
                flash(f"Quiz '{quiz.title}' has been shared with you.", "info")
                return redirect(url_for('dashboard.dashboard_view'))
            
            # The quiz is not shared with this user
            flash("This quiz hasn't been shared with you or doesn't exist.", "error")
            
        return redirect(url_for('dashboard.dashboard_view'))

    except Exception as e:
        current_app.logger.error(f"Authorization error: {e}")
        return "Authorization failed.", 500

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('quiz_routes.home'))

# This function has been moved to quiz_routes.py to be accessible at root URL
# @auth_bp.route('/check_login')
# def check_login():
#     return jsonify({'logged_in': current_user.is_authenticated})