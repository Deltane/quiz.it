"""
Test SendGrid email functionality for quiz.it
"""
from app import create_app
from app.utils.email_utils import send_email, logger
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.DEBUG)

def test_sendgrid():
    recipient = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    
    try:
        app = create_app()
        print("App created successfully")
        
        with app.app_context():
            print("\n----- Email Configuration -----")
            print(f"SendGrid API Key: {'*' * 10 + app.config.get('SENDGRID_API_KEY')[-5:] if app.config.get('SENDGRID_API_KEY') else 'Not Set'}")
            print(f"Default Sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
            
            print(f"\nSending test email to: {recipient}")
            
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Email</title>
            </head>
            <body>
                <h1>Test Email from Quiz.it</h1>
                <p>This is a test email to verify that SendGrid integration is working.</p>
                <p>If you received this, the email system is working correctly!</p>
            </body>
            </html>
            """
            
            result = send_email(
                subject="Test Email from Quiz.it via SendGrid",
                recipients=[recipient],
                body="This is a test email from Quiz.it to verify SendGrid email functionality.",
                html=html_content
            )
            
            if result:
                print("\n✅ Email sent successfully via SendGrid!")
            else:
                print("\n❌ Failed to send email")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_sendgrid()
