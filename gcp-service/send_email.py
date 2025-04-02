import functions_framework
import os
import sendgrid
from sendgrid.helpers.mail import Mail
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def send_email(request):
    """
    Cloud Function to send emails via SendGrid (HTTP trigger)
    """
    try:
        # Parse incoming request data
        request_json = request.get_json(silent=True)
        logger.info(f"Raw request data: {request.data}")
        logger.info(f"Parsed JSON: {request_json}")

        if not request_json:
            raise ValueError("No valid JSON payload received")

        # Use SendGrid to send the email
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        
        mail = Mail(
            from_email=os.environ.get("SENDER_EMAIL", "m22aie218@iitj.ac.in"),
            to_emails=os.environ.get("RECIPIENT_EMAIL", "esuvmul@gmail.com"),
            subject="VCC Alert from GCP",
            html_content=f"<strong>Network Configuration Update:</strong><br>{json.dumps(request_json, indent=2)}",
        )
        
        response = sg.send(mail)
        logger.info(f"Email sent - Status: {response.status_code}, Headers: {response.headers}")
        return f"Email sent successfully! Status: {response.status_code}", 200

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500