from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_test_email():
    # Get API key from environment
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("❌ API Key not found in environment!")
        return
    
    print(f"Using API Key: {'*' * 10 + api_key[-5:]}")
    
    # Basic message
    message = Mail(
        from_email='quiz.it@outlook.com',
        to_emails='test@example.com',
        subject='Minimal SendGrid Test',
        html_content='<strong>This is a test email using SendGrid</strong>'
    )
    
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"✅ Email sent! Status code: {response.status_code}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_test_email()
