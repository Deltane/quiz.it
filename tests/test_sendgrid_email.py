"""
Test script to verify that SendGrid email functionality is working correctly.
"""
import sys
import os
from app import create_app
from app.utils.email_utils import send_email
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_sendgrid')

def test_sendgrid_email():
    """
    Test SendGrid email functionality by sending a test email.
    
    Usage: python test_sendgrid_email.py [recipient_email]
    If no recipient email is provided, it will default to test@example.com.
    """
    # Get recipient email from command line args or use default
    recipient = sys.argv[1] if len(sys.argv) > 1 else 'test@example.com'
    
    try:
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Check SendGrid configuration
            logger.info("Checking SendGrid configuration...")
            sendgrid_api_key = app.config.get('SENDGRID_API_KEY')
            default_sender = app.config.get('MAIL_DEFAULT_SENDER')
            
            if not sendgrid_api_key:
                logger.error("SENDGRID_API_KEY not found in config!")
                return False
                
            if not default_sender:
                logger.error("MAIL_DEFAULT_SENDER not found in config!")
                return False
                
            logger.info(f"SendGrid API Key: {'✅ Found' if sendgrid_api_key else '❌ Missing'}")
            logger.info(f"Default Sender: {default_sender}")
                
            # Send test email
            logger.info(f"Sending test email to {recipient}")
            
            result = send_email(
                subject="Test Email from quiz.it (SendGrid)",
                recipients=[recipient],
                body=f"This is a test email sent using SendGrid to verify email functionality is working.",
                template='emails/quiz_share.html',
                sender_name="Quiz.it System Test",
                quiz_title="Test Quiz",
                login_url="http://example.com/login"
            )
            
            if result:
                logger.info(f"✅ Email successfully sent to {recipient}")
                return True
            else:
                logger.error(f"❌ Failed to send email to {recipient}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_sendgrid_email()
    sys.exit(0 if success else 1)
