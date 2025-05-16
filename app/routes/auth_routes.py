from flask import Blueprint, redirect, url_for, session, current_app, request, jsonify, flash
from flask_login import login_user, logout_user, current_user
from app import oauth, db
from app.models import User, Quiz, QuizShare, PendingQuizShare
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
        # Get the next parameter if it exists (for redirect after auth)
        next_url = request.args.get('next')
        
        redirect_uri = url_for('auth.authorize', _external=True)
        nonce = str(uuid.uuid4())
        state = str(uuid.uuid4())
        
        # Force the session to use secure cookie for authentication
        session.clear()  # Clear any existing session to avoid conflicts
        session.permanent = True  # Make sure session persists
        session['oauth_nonce'] = nonce
        session['oauth_state'] = state
        
        # If there's a next URL, store it for later redirection
        if next_url:
            session['next_url'] = next_url
            current_app.logger.info(f"Stored next_url for redirect after auth: {next_url}")
            
            # If next_url contains a quiz ID, store it as shared_quiz_id too
            if next_url.startswith('/') and next_url[1:].isdigit():
                quiz_id = int(next_url[1:])
                session['shared_quiz_id'] = quiz_id
                current_app.logger.info(f"Extracted and stored quiz_id from next_url: {quiz_id}")
        
        # Save session before redirecting
        session.modified = True
        
        return oauth.google.authorize_redirect(redirect_uri, nonce=nonce, state=state)
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return "Login failed.", 500

@auth_bp.route('/authorize')
def authorize():
    try:
        try:
            token = oauth.google.authorize_access_token()
        except Exception as e:
            current_app.logger.error(f"Error getting access token: {e}")
            # Check if we have a state mismatch
            if 'mismatching_state' in str(e):
                return redirect(url_for('auth.login'))  # Retry login if state mismatch
            raise
            
        nonce = session.pop('oauth_nonce', None)
        state = session.pop('oauth_state', None)
        if not nonce or not state:
            current_app.logger.error("Missing nonce or state in session")
            # Redirect to login instead of raising error
            return redirect(url_for('auth.login'))

        user_info = oauth.google.parse_id_token(token, nonce=nonce) or {}
        userinfo_response = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info.update(userinfo_response.json() or {})

        email = user_info.get("email")
        name = user_info.get("name", email)
        picture = user_info.get("picture", "") 

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                username=name,
                email=email,
                password_hash='google-oauth',
                picture=picture
            )
            db.session.add(user)
        else:
            # Update picture if changed or was not set before
            if user.picture != picture:
                user.picture = picture
        
        db.session.commit()

        login_user(user)
        session['user_id'] = user.id
        session['user_email'] = email
        session['user_name'] = name
        session['user_pic'] = picture
        
        # Check for any pending quiz shares for this email
        pending_shares = PendingQuizShare.query.filter_by(recipient_email=email).all()
        
        # Convert pending shares to actual shares
        for pending in pending_shares:
            new_share = QuizShare(
                quiz_id=pending.quiz_id,
                shared_with_user_id=user.id,
                shared_by_user_id=pending.shared_by_user_id
            )
            db.session.add(new_share)
            db.session.delete(pending)
        
        db.session.commit()

        # Check if there's a shared quiz to handle after login
        # Use get instead of pop to first check if it exists before removing it
        shared_quiz_id = session.get('shared_quiz_id')
        if shared_quiz_id:
            current_app.logger.info(f"Handling shared quiz after login: {shared_quiz_id}")
            
            # Now remove it from session since we're processing it
            session.pop('shared_quiz_id', None)
            
            # Check if the quiz exists
            shared_quiz = Quiz.query.get(shared_quiz_id)
            if shared_quiz:
                # First, check if a share entry already exists
                quiz_share = QuizShare.query.filter_by(
                    quiz_id=shared_quiz_id,
                    shared_with_user_id=user.id
                ).first()
                
                sender_id = None
                
                if not quiz_share:
                    # Check for pending share
                    pending_share = PendingQuizShare.query.filter_by(
                        quiz_id=shared_quiz_id,
                        recipient_email=email
                    ).first()
                    
                    if pending_share:
                        sender_id = pending_share.shared_by_user_id
                        # Convert pending to regular share
                        quiz_share = QuizShare(
                            quiz_id=shared_quiz_id,
                            shared_with_user_id=user.id,
                            shared_by_user_id=sender_id
                        )
                        db.session.add(quiz_share)
                        db.session.delete(pending_share)
                        db.session.commit()
                    else:
                        # Check if it's shared by someone else
                        quiz_creator = User.query.get(shared_quiz.user_id)
                        if quiz_creator and quiz_creator.id != user.id:
                            sender_id = quiz_creator.id
                            # Auto-create a share entry if it doesn't exist
                            quiz_share = QuizShare(
                                quiz_id=shared_quiz_id,
                                shared_with_user_id=user.id,
                                shared_by_user_id=sender_id
                            )
                            db.session.add(quiz_share)
                            db.session.commit()
                else:
                    sender_id = quiz_share.shared_by_user_id
                
                # Set up the shared quiz modal to display on dashboard
                session['show_shared_quiz_modal'] = True
                session['shared_quiz_id'] = shared_quiz_id
                session['shared_quiz_title'] = shared_quiz.title
                session['shared_quiz_description'] = getattr(shared_quiz, 'description', '')  # Add description to session
                
                if sender_id:
                    session['shared_quiz_sender_id'] = sender_id
                    # Get sender's name for the modal
                    sender = User.query.get(sender_id)
                    if sender:
                        session['shared_quiz_sender_name'] = sender.username
                
                # Make sure session is saved
                session.modified = True
                
                current_app.logger.info(f"Shared quiz processed, redirecting to dashboard with modal. Session: {session}")
                
                # Redirect to the dashboard which will show the modal
                return redirect(url_for('dashboard.dashboard_view'))

        # Check for a quiz ID in localStorage as backup (added via auth_loading.html)

        # Check if there's a next URL to redirect to
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
            
        # Default redirect to dashboard
        return redirect(url_for('dashboard.dashboard_view'))

    except Exception as e:
        current_app.logger.error(f"Authorization error: {e}")
        return "Authorization failed.", 500

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('quiz_routes.home'))
