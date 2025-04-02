import functions_framework
import os
import sendgrid
from sendgrid.helpers.mail import Mail
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def send_email(cloud_event):
    """
    Cloud Function to send emails via SendGrid.
    """
    try:
        message = json.loads(cloud_event.data.decode('utf-8'))
        logger.info(f"Received email message: {message}")

        # Use SendGrid to send the email
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        mail = Mail(
            from_email="your-email@example.com",
            to_emails="recipient@example.com",
            subject="Email from GCP",
            html_content=f"<strong>{message}</strong>",
        )
        response = sg.send(mail)
        logger.info(f"Email sent with status code: {response.status_code}")

    except Exception as e:
        logger.error(f"Error sending email: {e}")