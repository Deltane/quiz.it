"""
Simple test for email functionality with detailed error handling
"""
import traceback
import sys
from app import create_app, mail
from flask_mail import Message

def simple_test():
    recipient = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    
    try:
        app = create_app()
        print("App created successfully")
        
        with app.app_context():
            print("\n----- Mail Configuration -----")
            print(f"Server: {app.config.get('MAIL_SERVER')}")
            print(f"Port: {app.config.get('MAIL_PORT')}")
            print(f"Username: {app.config.get('MAIL_USERNAME')}")
            print(f"Password: {'*' * 6 if app.config.get('MAIL_PASSWORD') else 'Not Set'}")
            print(f"Use TLS: {app.config.get('MAIL_USE_TLS')}")
            print(f"Default Sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
            
            print("\n----- Testing Direct Email Send -----")
            print(f"Sending test email to: {recipient}")
            
            try:
                msg = Message(
                    subject="Test Email from Quiz.it",
                    recipients=[recipient],
                    body="This is a test email from Quiz.it.",
                    sender=app.config.get('MAIL_DEFAULT_SENDER')
                )
                mail.send(msg)
                print("✅ Email sent successfully!")
            except Exception as e:
                print(f"❌ Email sending failed: {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error creating app: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
