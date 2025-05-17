"""
Test email functionality for quiz.it
"""
from app import create_app, mail
from app.utils.email_utils import send_email
from flask_mail import Message

def test_email():
    app = create_app()
    with app.app_context():
        app.logger.info('Trying to send a test email')
        try:
            # Test if mail is configured properly
            print('Mail settings:')
            print(f'  Server: {app.config.get("MAIL_SERVER")}')
            print(f'  Port: {app.config.get("MAIL_PORT")}')
            print(f'  Username: {"Set" if app.config.get("MAIL_USERNAME") else "Not set"}')
            print(f'  Password: {"Set" if app.config.get("MAIL_PASSWORD") else "Not set"}')
            
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
            print(f'Failed to send email: {str(e)}')
            app.logger.error(f'Failed to send email: {str(e)}')

if __name__ == '__main__':
    test_email()
