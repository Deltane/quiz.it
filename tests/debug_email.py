"""
Debug email functionality for quiz.it
"""
from app import create_app, mail
from app.utils.email_utils import send_email
import traceback
import sys

def debug_email():
    app = create_app()
    with app.app_context():
        app.logger.info('Debugging email functionality')
        try:
            # Print mail configuration
            print('Mail configuration:')
            print(f'  Server: {app.config.get("MAIL_SERVER")}')
            print(f'  Port: {app.config.get("MAIL_PORT")}')
            print(f'  Username: {app.config.get("MAIL_USERNAME")}')
            print(f'  Password: {"*" * 8 if app.config.get("MAIL_PASSWORD") else "Not set"}')
            print(f'  Use TLS: {app.config.get("MAIL_USE_TLS")}')
            print(f'  Default Sender: {app.config.get("MAIL_DEFAULT_SENDER")}')
            
            # Get test recipient from command line or use default
            recipient = sys.argv[1] if len(sys.argv) > 1 else 'test@example.com'
            print(f'\nSending test email to: {recipient}\n')
            
            # Send a test email using the utility function
            result = send_email(
                subject='Test Email from quiz.it',
                recipients=[recipient], 
                body='This is a test email from quiz.it to verify email functionality.',
                template='emails/quiz_share.html',
                sender_name='Quiz.it System',
                quiz_title='Test Quiz',
                login_url='http://example.com/login'
            )
            
            if result:
                print('\n✅ Email sent successfully!')
            else:
                print('\n❌ Failed to send email, but no exception was raised.')
                
        except Exception as e:
            print(f'\n❌ ERROR: {str(e)}')
            print('\nDetailed traceback:')
            traceback.print_exc()

if __name__ == '__main__':
    debug_email()
