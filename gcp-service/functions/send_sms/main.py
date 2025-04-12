import functions_framework
import os
import logging
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def send_sms(cloud_event):
    """Triggered by Cloud Storage upload"""
    try:
        # Extract file metadata
        data = cloud_event.data
        file_name = data["name"]
        bucket_name = data["bucket"]
        
        logger.info(f"New upload: {file_name} in {bucket_name}")

        # Twilio credentials
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_FROM_NUMBER']
        to_number = os.environ['SMS_RECIPIENT']

        # Send SMS
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"New file uploaded to GCP: {file_name}",
            from_=from_number,
            to=to_number
        )

        logger.info(f"SMS sent! SID: {message.sid}")
        return "Notification sent successfully"

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise