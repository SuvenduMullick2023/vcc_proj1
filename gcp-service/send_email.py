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
    Returns JSON response with operation details
    """
    try:
        request_json = request.get_json(silent=True)
        logger.info(f"Email request data: {request.data}")

        if not request_json:
            logger.error("No JSON payload received")
            return {"status": "error", "message": "No JSON payload"}, 400

        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        
        mail = Mail(
            from_email="m22aie218@iitj.ac.in" #os.environ.get("SENDER_EMAIL"),
            to_emails="esuvmul@gmail.com" #os.environ.get("RECIPIENT_EMAIL"),
            subject="VCC Alert",
            html_content=f"<strong>Network Update:</strong><br>{json.dumps(request_json)}"
        )
        
        response = sg.send(mail)
        logger.info(f"Email sent - Status: {response.status_code}")
        
        return {
            "status": "success",
            "service": "email",
            "status_code": response.status_code,
            "message": "Email queued for delivery"
        }, 200

    except Exception as e:
        logger.error(f"Email error: {str(e)}")
        return {
            "status": "error",
            "service": "email",
            "message": str(e)
        }, 500