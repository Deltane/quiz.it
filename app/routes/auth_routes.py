from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Add logic to authenticate the user (e.g., check username and password)
        # Example:
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Assuming `check_password` is implemented
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))  # Replace 'main.dashboard' with your target route
        else:
            flash('Invalid username or password', 'danger')

    #Debug statement to confirm the route is being accessed
    print("Rendering login.html")
    return render_template('login.html')

# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         # Handle registration form (stub)
#         pass
#     return render_template('register.html')
