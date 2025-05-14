from app import create_app, mail
from flask_mail import Message

app = create_app()
with app.app_context():
    print('Mail settings:')
    print(f'Server: {app.config.get("MAIL_SERVER")}')
    print(f'Port: {app.config.get("MAIL_PORT")}')
    print(f'Username: {app.config.get("MAIL_USERNAME")}')
    print(f'Password: {"Set" if app.config.get("MAIL_PASSWORD") else "Not set"}')
    print(f'Default Sender: {app.config.get("MAIL_DEFAULT_SENDER")}')
    print(f'USE_TLS: {app.config.get("MAIL_USE_TLS")}')
