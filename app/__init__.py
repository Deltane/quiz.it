from dotenv import load_dotenv
import os
# import shutil

load_dotenv()  # Load environment variables from .env

from flask import Flask
from app.extensions import db, migrate, session_manager, oauth
import requests


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Load secret key
    app.secret_key = os.getenv('SECRET_KEY')  # Load SECRET_KEY from .env
    if not app.secret_key:
        raise ValueError("SECRET_KEY environment variable not set")

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Flask-Session config
    app.config['SESSION_TYPE'] = 'filesystem'  # <- Important for server-side sessions
    session_manager.init_app(app)  # <- Correctly initialize server-side session
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)

    # Create all tables after initializing db and migrate
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created.")

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

    # Register blueprints
    from app.routes.quiz_routes import quiz_routes
    from app.routes.auth_routes import auth_bp
    from app.routes.ai_routes import ai_routes
    from app.routes.dashboard_routes import dashboard_bp
    app.register_blueprint(quiz_routes)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ai_routes)
    app.register_blueprint(dashboard_bp)

    # app.register_blueprint(stats_bp)

    from app import models
    return app