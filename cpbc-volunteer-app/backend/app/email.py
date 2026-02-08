import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
ADMIN_NOTIFICATION_EMAIL = os.getenv("ADMIN_NOTIFICATION_EMAIL", "")


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send a password reset email via SMTP with TLS.
    Returns True on success, False on failure. Fails gracefully.
    """
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL]):
        logger.warning("SMTP not configured - logging reset link to console")
        reset_link = f"https://volunteer.crosspointbaptistchurchbc.com/admin?reset_token={reset_token}"
        logger.info(f"Password reset link for {to_email}: {reset_link}")
        return False

    reset_link = f"https://volunteer.crosspointbaptistchurchbc.com/admin?reset_token={reset_token}"

    subject = "Password Reset - CPBC Volunteer App"

    text_body = f"""Password Reset Request

You requested a password reset for the CPBC Volunteer App admin dashboard.

Click the link below to set a new password (valid for 1 hour):
{reset_link}

If you did not request this, please ignore this email.

---
Cross Point Baptist Church Volunteer App"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c5282; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f7fafc; }}
        .button {{ display: inline-block; background-color: #2c5282; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 5px;
                   margin: 16px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #718096; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Password Reset</h1></div>
        <div class="content">
            <p>You requested a password reset for the CPBC Volunteer App admin dashboard.</p>
            <p>Click the button below to set a new password. This link is valid for 1 hour.</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button"
                   style="color: white;">Reset Password</a>
            </p>
            <p style="font-size: 12px; color: #718096;">
                If the button doesn't work, copy and paste this link:<br>
                {reset_link}
            </p>
            <p>If you did not request this reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Cross Point Baptist Church Volunteer App</p>
        </div>
    </div>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
        reset_link = f"https://volunteer.crosspointbaptistchurchbc.com/admin?reset_token={reset_token}"
        logger.info(f"Password reset link for {to_email}: {reset_link}")
        return False


def send_volunteer_notification_email(
    to_emails: list[str],
    volunteer_name: str,
    volunteer_email: str,
    volunteer_phone: str,
    ministries: list[dict],
) -> bool:
    """
    Send email notification to admins when a new volunteer signs up.
    Returns True on success, False on failure. Fails gracefully.

    Args:
        to_emails: List of admin email addresses to notify
        volunteer_name: Volunteer's full name
        volunteer_email: Volunteer's email address
        volunteer_phone: Volunteer's phone number
        ministries: List of dicts with 'ministry_area' and 'category' keys
    """
    if not to_emails:
        logger.warning("No notification recipients - skipping volunteer notification")
        return False

    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL]):
        logger.warning("SMTP not configured - logging volunteer signup to console")
        ministry_list = ", ".join([m["ministry_area"] for m in ministries])
        logger.info(
            f"New volunteer signup: {volunteer_name} ({volunteer_email}, "
            f"{volunteer_phone}) - Ministries: {ministry_list}"
        )
        return False

    subject = f"New Volunteer Signup: {volunteer_name}"

    ministry_text = "\n".join(
        [f"  - {m['ministry_area']} ({m['category']})" for m in ministries]
    )

    text_body = f"""New Volunteer Signup

A new volunteer has signed up through the CPBC Volunteer App.

Volunteer Information:
----------------------
Name: {volunteer_name}
Phone: {volunteer_phone}
Email: {volunteer_email}

Ministry Areas Selected:
------------------------
{ministry_text}

View all volunteers in the admin dashboard:
https://volunteer.crosspointbaptistchurchbc.com/admin

---
Cross Point Baptist Church Volunteer App"""

    ministry_html = "".join(
        [
            f'<div style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">'
            f"<strong>{m['ministry_area']}</strong> "
            f"<em style=\"color: #718096;\">({m['category']})</em></div>"
            for m in ministries
        ]
    )

    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c5282; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f7fafc; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        .info-table td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }}
        .info-label {{ font-weight: bold; color: #2c5282; width: 120px; }}
        .ministry-list {{ background-color: white; border-radius: 5px; overflow: hidden; margin: 12px 0; }}
        .button {{ display: inline-block; background-color: #2c5282; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 5px;
                   margin: 16px 0; }}
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

            <h2 style="color: #2c5282; font-size: 18px;">Volunteer Information</h2>
            <table class="info-table">
                <tr>
                    <td class="info-label">Name</td>
                    <td>{volunteer_name}</td>
                </tr>
                <tr>
                    <td class="info-label">Phone</td>
                    <td>{volunteer_phone}</td>
                </tr>
                <tr>
                    <td class="info-label">Email</td>
                    <td><a href="mailto:{volunteer_email}">{volunteer_email}</a></td>
                </tr>
            </table>

            <h2 style="color: #2c5282; font-size: 18px;">Ministry Areas Selected</h2>
            <div class="ministry-list">
                {ministry_html}
            </div>

            <p style="text-align: center;">
                <a href="https://volunteer.crosspointbaptistchurchbc.com/admin" class="button"
                   style="color: white;">View Admin Dashboard</a>
            </p>
        </div>
        <div class="footer">
            <p>Cross Point Baptist Church Volunteer App</p>
        </div>
    </div>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = ", ".join(to_emails)
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Volunteer notification email sent to {', '.join(to_emails)}")
        return True
    except Exception as e:
        logger.error(f"Failed to send volunteer notification email: {str(e)}")
        ministry_list = ", ".join([m["ministry_area"] for m in ministries])
        logger.info(
            f"New volunteer signup: {volunteer_name} ({volunteer_email}, "
            f"{volunteer_phone}) - Ministries: {ministry_list}"
        )
        return False
