from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from authlib.integrations.flask_client import OAuth
import requests
from flask_login import LoginManager
# Removed Flask-Mail import

# Initialize extensions globally
db = SQLAlchemy()
# Removed mail = Mail()
migrate = Migrate()
session_manager = Session()
oauth = OAuth()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Load secret key
    app.secret_key = os.getenv('SECRET_KEY')  # Load SECRET_KEY from .env
    if not app.secret_key:
        raise ValueError("SECRET_KEY environment variable not set")

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # SendGrid Email config
    app.config['SENDGRID_API_KEY'] = os.getenv('SENDGRID_API_KEY')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'quiz.it <quiz.it@outlook.com>')
    
    # Log email configuration status
    app.logger.info("SendGrid API configured")
    app.logger.info(f"API Key provided: {'Yes' if app.config['SENDGRID_API_KEY'] else 'No'}")
    app.logger.info(f"Default sender: {app.config['MAIL_DEFAULT_SENDER']}")

    # Flask-Session config
    app.config['SESSION_TYPE'] = 'filesystem'  # <- Important for server-side sessions
    session_manager.init_app(app)  # <- Correctly initialize server-side session
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    login_manager.init_app(app)
    # Removed Flask-Mail initialization

    # Log app initialization
    app.logger.info("Flask app initialized with configuration:")
    app.logger.info("SECRET_KEY: {'Set' if app.secret_key else 'Not Set'}")
    app.logger.info("DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Check for Google OAuth environment variables
    google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    if not google_client_id or not google_client_secret:
        app.logger.error("GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET environment variable not set")
        raise ValueError("GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET environment variable not set")

    # Configure OAuth
    from app.routes.auth_routes import init_oauth
    init_oauth(oauth)

    # Configure login manager
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes.quiz_routes import quiz_routes
    from app.routes.auth_routes import auth_bp
    from app.routes.ai_routes import ai_routes
    from app.routes.stats_routes import stats_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.profile_routes import profile_bp # Import the new profile blueprint

    app.register_blueprint(quiz_routes)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ai_routes)
    app.register_blueprint(stats_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp) # Register the profile blueprint

    from datetime import timedelta
    from flask import session

    # Set session lifetime
    app.permanent_session_lifetime = timedelta(minutes=30)

    @app.before_request
    def refresh_session_if_logged_in():
        if session.get('user_email'):  # or use Flask-Login's current_user.is_authenticated
            session.permanent = True

    from app import models
    return app
