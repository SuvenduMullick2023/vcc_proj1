import functions_framework
import os
import logging
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def send_sms(cloud_event):
    """
    Cloud Function triggered by GCS upload events
    Sends SMS with uploaded filename using Twilio
    """
    try:
        # Extract bucket metadata from CloudEvent
        event_data = cloud_event.data
        bucket_name = event_data.get("bucket")
        filename = event_data.get("name")
        
        if not filename:
            logger.error("No filename found in event data")
            return

        logger.info(f"New upload detected: {filename} in {bucket_name}")

        # Get Twilio credentials from environment
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_FROM_NUMBER']
        to_number = os.environ['SMS_RECIPIENT']

        # Create Twilio client
        client = Client(account_sid, auth_token)

        # Create SMS message
        message = client.messages.create(
            body=f"New file uploaded: {filename}",
            from_=from_number,
            to=to_number
        )

        logger.info(f"SMS sent successfully! SID: {message.sid}")
        return "SMS triggered successfully"

    except KeyError as e:
        logger.error(f"Missing environment variable: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing SMS request: {str(e)}")
        raise