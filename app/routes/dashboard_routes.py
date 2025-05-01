from flask import Blueprint, render_template, session

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
def dashboard_view():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))
    return render_template("dashboard.html")
