from flask import current_app, render_template
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

# Set up a dedicated logger for email operations
logger = logging.getLogger('email_utils')

def send_email(subject, recipients, body, html=None, template=None, **kwargs):
    """
    Send an email using SendGrid API with optional HTML content or template rendering.
    
    Args:
        subject: Email subject
        recipients: List of recipient emails
        body: Plain text email body
        html: HTML content (optional)
        template: HTML template path (optional)
        **kwargs: Template variables for rendering
    """
    try:
        # If template is provided, render it with kwargs
        html_content = None
        if template:
            html_content = render_template(template, **kwargs)
        elif html:
            html_content = html
            
        # Log before sending
        logger.info(f"Attempting to send email to: {recipients}")
        
        # Get SendGrid API key
        api_key = current_app.config.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY not found in configuration")
            return False
            
        # Create mail message
        from_email = current_app.config.get('MAIL_DEFAULT_SENDER')
        sender_email = from_email
        if '<' in from_email:
            # Extract email from format like "Quiz.it <quiz.it@outlook.com>"
            sender_email = from_email.split('<')[1].replace('>', '').strip()
            
        logger.info(f"Using sender email: {sender_email}")
            
        for recipient in recipients:
            try:
                # Create a personalized mail message following SendGrid's expected format
                message = Mail(
                    from_email=sender_email,
                    to_emails=recipient,
                    subject=subject
                )
                
                # Add content in the proper format
                if html_content:
                    message.add_content(Content("text/plain", body))
                    message.add_content(HtmlContent(html_content))
                else:
                    message.add_content(Content("text/plain", body))
                
                # Log the mail object being sent (for debugging)
                logger.info(f"Prepared message: sender={sender_email}, recipient={recipient}, subject={subject}")
                    
                # Send the email using SendGrid
                sg = SendGridAPIClient(api_key)
                response = sg.send(message)
                
                # Log success with more details
                status_code = response.status_code
                logger.info(f"Email sent to {recipient}, status code: {status_code}, body: {response.body}, headers: {response.headers}")
                
                if status_code < 200 or status_code >= 300:
                    logger.error(f"SendGrid returned non-success status: {status_code}")
                    logger.error(f"Response body: {response.body}")
                    return False
                    
            except Exception as inner_e:
                logger.error(f"Error sending to {recipient}: {str(inner_e)}")
                return False
        
        return True
    except Exception as e:
        import traceback
        logger.error(f"Error sending email: {str(e)}")
        logger.error(traceback.format_exc())
        return False
