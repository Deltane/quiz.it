from app import create_app, mail
from app.utils.email_utils import send_email
import traceback

app = create_app()
with app.app_context():
    try:
        # Print configuration
        print('Mail settings:')
        print(f'Server: {app.config.get("MAIL_SERVER")}')
        print(f'Port: {app.config.get("MAIL_PORT")}')
        print(f'Username: {app.config.get("MAIL_USERNAME")}')
        print(f'Password: {"Set" if app.config.get("MAIL_PASSWORD") else "Not set"}')
        print(f'Default Sender: {app.config.get("MAIL_DEFAULT_SENDER")}')
        print(f'USE_TLS: {app.config.get("MAIL_USE_TLS")}')
        
        # Use the send_email utility
        result = send_email(
            subject='Test Email from quiz.it',
            recipients=['test@example.com'], 
            body='This is a test email body',
            template='emails/quiz_share.html',
            sender_name='Test User',
            quiz_title='Test Quiz',
            login_url='http://example.com'
        )
        print(f'Email send result: {result}')
    except Exception as e:
        print(f'ERROR: {str(e)}')
        traceback.print_exc()
