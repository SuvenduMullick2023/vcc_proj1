import functions_framework
import os
import logging
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def send_sms(cloud_event):
    """Triggered by Cloud Storage object upload or deletion"""
    try:
        # Extract metadata
        data = cloud_event.data
        event_type = cloud_event["ce_type"]  # e.g., google.storage.object.finalize or delete
        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")
        size = data.get("size", "N/A")
        content_type = data.get("contentType", "N/A")
        time_created = data.get("timeCreated", "N/A")
        updated = data.get("updated", "N/A")
        storage_class = data.get("storageClass", "N/A")

        # Determine action type
        action = "uploaded to" if "finalize" in event_type else "deleted from" if "delete" in event_type else "changed in"

        logger.info(f"File {file_name} was {action} {bucket_name}")

        # Compose SMS body
        body = (
            f"GCS Alert: File {action} {bucket_name}\n"
            f"Name: {file_name}\n"
            f"Type: {content_type}\n"
            f"Size: {size} bytes\n"
            f"Created: {time_created}\n"
            f"Updated: {updated}\n"
            f"Storage: {storage_class}"
        )

        # Twilio credentials
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_FROM_NUMBER']
        to_number = os.environ['SMS_RECIPIENT']

        # Send SMS
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )

        logger.info(f"SMS sent! SID: {message.sid}")
        return "Notification sent successfully"

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise