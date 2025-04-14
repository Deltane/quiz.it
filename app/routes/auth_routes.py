from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login form (stub)
        pass
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle registration form (stub)
        pass
    return render_template('register.html')
