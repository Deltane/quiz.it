from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask_dance.contrib.google import make_google_blueprint
from flask_session import Session

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Load config
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizapp.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init plugins
    db.init_app(app)
    # login_manager.init_app(app)
    Migrate(app, db)

    google_bp = make_google_blueprint(
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        redirect_to="auth.google_callback",
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    # from app.routes.quiz_routes import quiz_bp
    # from app.routes.ai_routes import ai_bp
    # from app.routes.stats_routes import stats_bp

    app.register_blueprint(auth_bp)
    # app.register_blueprint(quiz_bp)
    # app.register_blueprint(ai_bp)
    # app.register_blueprint(stats_bp)

    return app
