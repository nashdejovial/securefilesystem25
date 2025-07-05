from flask_mail import Message
from app.extensions import mail
from flask import current_app, render_template
from datetime import datetime
import requests


def check_url_accessibility(url):
    """Check if a URL is accessible."""
    try:
        response = requests.head(url, timeout=2)
        return response.status_code < 400
    except:
        return False


def get_accessible_frontend_url():
    """Get the first accessible frontend URL from the configured list."""
    # First try the primary configured URL
    primary_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    if check_url_accessibility(primary_url):
        return primary_url

    # If primary URL is not accessible, try alternatives
    for url in current_app.config.get('FRONTEND_URLS', []):
        if check_url_accessibility(url):
            return url

    # If no URLs are accessible, return the primary URL as fallback
    return primary_url


def send_confirmation_email(recipient, confirm_url, name=None):
    """
    Send a confirmation email to the user.
    
    Args:
        recipient (str): The recipient's email address
        confirm_url (str): The confirmation URL
        name (str, optional): The recipient's name. Defaults to None.
    """
    msg = Message("Confirm Your Email - Secure File Sharing System",
                  sender=current_app.config.get('MAIL_USERNAME', 'noreply@filesharing.com'),
                  recipients=[recipient])

    # Prepare template context
    context = {
        'confirm_url': confirm_url,
        'name': name or recipient.split('@')[0],  # Use email username if name not provided
        'year': datetime.utcnow().year
    }

    msg.body = f"""Hello {context['name']},

Thank you for registering with our Secure File Sharing System!

Please click the following link to confirm your email address:

{confirm_url}

If you did not create this account, please ignore this email.

Best regards,
Secure File Sharing Team

---
This is an automated message, please do not reply to this email.
© {context['year']} Secure File Sharing System. All rights reserved."""

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send confirmation email: {str(e)}')
        raise


def send_verification_email(recipient, token, name=None):
    """
    Send a verification email to the user.
    
    Args:
        recipient (str): The recipient's email address
        token (str): The verification token
        name (str, optional): The recipient's name. Defaults to None.
    """
    msg = Message("Verify Your Email - Secure File Sharing System",
                  sender=current_app.config.get('MAIL_USERNAME', 'noreply@filesharing.com'),
                  recipients=[recipient])

    # Get an accessible frontend URL
    base_url = get_accessible_frontend_url()
    verify_url = f"{base_url}/verify-email/{token}"

    # Prepare template context
    context = {
        'verify_url': verify_url,
        'name': name or recipient.split('@')[0],  # Use email username if name not provided
        'year': datetime.utcnow().year
    }

    msg.body = f"""Hello {context['name']},

Please click the following link to verify your email address:

{verify_url}

If you did not request this verification, please ignore this email.

Best regards,
Secure File Sharing Team

---
This is an automated message, please do not reply to this email.
© {context['year']} Secure File Sharing System. All rights reserved."""

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send verification email: {str(e)}')
        raise


def send_reset_email(recipient, token):
    """Send a password reset email to the user."""
    msg = Message("Reset Your Password - Secure File Sharing System",
                  sender=current_app.config.get('MAIL_USERNAME', 'noreply@filesharing.com'),
                  recipients=[recipient])

    # Get an accessible frontend URL
    base_url = get_accessible_frontend_url()
    reset_url = f"{base_url}/reset-password/{token}"

    # Prepare template context
    context = {
        'reset_url': reset_url,
        'name': recipient.split('@')[0],
        'year': datetime.utcnow().year
    }

    msg.body = f"""Hello {context['name']},

You have requested to reset your password. Click the following link to proceed:

{reset_url}

If you did not request this password reset, please ignore this email.

Best regards,
Secure File Sharing Team

---
This is an automated message, please do not reply to this email.
© {context['year']} Secure File Sharing System. All rights reserved."""

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send reset email: {str(e)}')
        raise

