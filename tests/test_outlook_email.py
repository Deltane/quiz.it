"""
Outlook-specific email test
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv('MAIL_SERVER', 'smtp-mail.outlook.com')
SMTP_PORT = int(os.getenv('MAIL_PORT', 587))
USERNAME = os.getenv('MAIL_USERNAME', 'quiz.it@outlook.com')
PASSWORD = os.getenv('MAIL_PASSWORD', '')
SENDER = os.getenv('MAIL_DEFAULT_SENDER', USERNAME)
RECIPIENT = "test@example.com"  # Change to a real email for testing

print(f"Using SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Username: {USERNAME}")
print(f"Password: {'*' * 8 if PASSWORD else 'Not Set'}")
print(f"Sender: {SENDER}")
print(f"Recipient: {RECIPIENT}")

# Create message
msg = MIMEMultipart()
msg['From'] = SENDER
msg['To'] = RECIPIENT
msg['Subject'] = "Test Email from Quiz.it (Direct SMTP)"

# Add body
body = "This is a test email sent directly via SMTP from the Quiz.it application."
msg.attach(MIMEText(body, 'plain'))

# Send email
try:
    print("\nConnecting to SMTP server...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    
    print("Starting TLS...")
    server.starttls()
    server.ehlo()
    
    print(f"Logging in as {USERNAME}...")
    server.login(USERNAME, PASSWORD)
    
    print("Sending email...")
    server.send_message(msg)
    
    print("✅ Email sent successfully!")
    
    server.quit()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    traceback.print_exc()
