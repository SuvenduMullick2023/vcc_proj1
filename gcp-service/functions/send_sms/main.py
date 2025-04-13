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
        # Extract metadata from cloud_event
        data = cloud_event.data
        event_type = cloud_event["type"]  # Ex: google.storage.object.finalize or google.storage.object.delete
        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")

        # Define default values to avoid KeyError
        size = data.get("size", "N/A")
        content_type = data.get("contentType", "N/A")
        time_created = data.get("timeCreated", "N/A")
        updated = data.get("updated", "N/A")
        storage_class = data.get("storageClass", "N/A")

        # Determine type of action
        if "finalize" in event_type:
            action = "uploaded to"
        elif "delete" in event_type:
            action = "deleted from"
        else:
            action = "changed in"

        logger.info(f"File {file_name} was {action} bucket {bucket_name}")

        # Compose SMS body
        body = (
            f"GCS Alert: File {action} {bucket_name}\n"
            f"📄 Name: {file_name}\n"
            f"📦 Type: {content_type}\n"
            f"📏 Size: {size} bytes\n"
            f"🕒 Created: {time_created}\n"
            f"🕒 Updated: {updated}\n"
            f"🏷️ Storage Class: {storage_class}"
        )

        # Load Twilio credentials from environment variables
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        from_number = os.environ["TWILIO_FROM_NUMBER"]
        to_number = os.environ["SMS_RECIPIENT"]

        # Send SMS using Twilio
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )

        logger.info(f"✅ SMS sent successfully! SID: {message.sid}")
        return "SMS notification sent successfully"

    except Exception as e:
        logger.error(f"❌ Error in send_sms: {str(e)}")
        raise
