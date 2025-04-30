from flask import Blueprint, render_template, session

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
def show_dashboard():
    return render_template("dashboard.html", user=session.get("user_email"))