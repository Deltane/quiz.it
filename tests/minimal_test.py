import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()

# Print environment variables
print("Environment variables:")
for key in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']:
    value = os.environ.get(key)
    if key == 'MAIL_PASSWORD' and value:
        value = '******'
    print(f"  {key}: {value}")

# Create simple Flask app
app = Flask(__name__)

# Configure mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp-mail.outlook.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))

# Initialize mail
mail = Mail(app)

# Print Flask app config
print("\nFlask app mail config:")
for key in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_DEFAULT_SENDER', 'MAIL_USE_TLS']:
    print(f"  {key}: {app.config.get(key)}")
print(f"  MAIL_PASSWORD: {'Set' if app.config.get('MAIL_PASSWORD') else 'Not Set'}")

# Try sending email
with app.app_context():
    try:
        msg = Message(
            subject='Test Email from Minimal Script',
            recipients=['test@example.com'],
            body='This is a test email from a minimal script.',
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        print("\nAttempting to send email...")
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
