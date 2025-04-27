from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_dance.contrib.google import make_google_blueprint
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions (without app)
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Load config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizapp.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize plugins
    Session(app)
    db.init_app(app)
    Migrate(app, db)

    # Register internal blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.quiz_routes import quiz_bp
    from app.routes.ai_routes import ai_routes

    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(ai_routes)

    # Create the Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ],
        redirect_to="auth.google_callback"
    )

    # Register Google blueprint
    app.register_blueprint(google_bp, url_prefix="/login/google")

    return app
