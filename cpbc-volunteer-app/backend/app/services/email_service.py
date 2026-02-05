import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# AWS SES Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL", "noreply@crosspointbc.org")
ADMIN_NOTIFICATION_EMAILS = os.getenv("ADMIN_NOTIFICATION_EMAILS", "").split(",")


def get_ses_client():
    """
    Get an AWS SES client.

    Returns:
        boto3 SES client or None if credentials not configured
    """
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.warning("AWS credentials not configured - email notifications disabled")
        return None

    try:
        import boto3
        client = boto3.client(
            "ses",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create SES client: {str(e)}")
        return None


def send_volunteer_notification(volunteer) -> bool:
    """
    Send email notification to admins when a new volunteer signs up.

    This function fails gracefully - if SES is not configured or the email
    fails to send, it logs the error but does not raise an exception.
    The volunteer signup should never fail because of an email issue.

    Args:
        volunteer: Volunteer model instance with ministries loaded

    Returns:
        True if email sent successfully, False otherwise
    """
    # Filter out empty emails from the list
    recipient_emails = [email.strip() for email in ADMIN_NOTIFICATION_EMAILS if email.strip()]

    if not recipient_emails:
        logger.warning("No admin notification emails configured - skipping notification")
        return False

    ses_client = get_ses_client()
    if ses_client is None:
        logger.warning("SES client not available - skipping volunteer notification email")
        return False

    # Build the ministry list for the email
    ministry_list = "\n".join([
        f"  - {m.ministry_area} ({m.category})"
        for m in volunteer.ministries
    ])

    # Format the signup date
    signup_time = volunteer.signup_date.strftime("%B %d, %Y at %I:%M %p")

    # Build the email content
    subject = f"New Volunteer Signup: {volunteer.name}"

    text_body = f"""
New Volunteer Signup

A new volunteer has signed up through the CPBC Volunteer App.

Volunteer Information:
----------------------
Name: {volunteer.name}
Phone: {volunteer.phone}
Email: {volunteer.email}
Signup Date: {signup_time}

Ministry Areas Selected:
------------------------
{ministry_list}

---
This is an automated notification from the CPBC Volunteer App.
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c5282; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f7fafc; }}
        .info-section {{ margin-bottom: 20px; }}
        .info-label {{ font-weight: bold; color: #2c5282; }}
        .ministry-list {{ background-color: white; padding: 15px; border-radius: 5px; }}
        .ministry-item {{ padding: 5px 0; border-bottom: 1px solid #e2e8f0; }}
        .ministry-item:last-child {{ border-bottom: none; }}
        .footer {{ text-align: center; padding: 20px; color: #718096; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Volunteer Signup</h1>
        </div>
        <div class="content">
            <p>A new volunteer has signed up through the CPBC Volunteer App.</p>

            <div class="info-section">
                <h2>Volunteer Information</h2>
                <p><span class="info-label">Name:</span> {volunteer.name}</p>
                <p><span class="info-label">Phone:</span> {volunteer.phone}</p>
                <p><span class="info-label">Email:</span> <a href="mailto:{volunteer.email}">{volunteer.email}</a></p>
                <p><span class="info-label">Signup Date:</span> {signup_time}</p>
            </div>

            <div class="info-section">
                <h2>Ministry Areas Selected</h2>
                <div class="ministry-list">
                    {"".join([f'<div class="ministry-item"><strong>{m.ministry_area}</strong> <em>({m.category})</em></div>' for m in volunteer.ministries])}
                </div>
            </div>
        </div>
        <div class="footer">
            <p>This is an automated notification from the CPBC Volunteer App.</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={
                "ToAddresses": recipient_emails
            },
            Message={
                "Subject": {
                    "Data": subject,
                    "Charset": "UTF-8"
                },
                "Body": {
                    "Text": {
                        "Data": text_body,
                        "Charset": "UTF-8"
                    },
                    "Html": {
                        "Data": html_body,
                        "Charset": "UTF-8"
                    }
                }
            }
        )

        logger.info(f"Volunteer notification email sent successfully. MessageId: {response['MessageId']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send volunteer notification email: {str(e)}")
        return False
