import os
import logging
from twilio.rest import Client
import functions_framework

# Configure logging
logging.basicConfig(level=logging.INFO)

@functions_framework.cloud_event
def send_sms(cloud_event):
    """Triggered by file upload to GCS"""
    try:
        data = cloud_event.data
        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")
        content_type = data.get("contentType", "N/A")
        size = data.get("size", "N/A")
        time_created = data.get("timeCreated", "N/A")
        #updated = data.get("updated", "N/A")
        #storage_class = data.get("storageClass", "N/A")

        body = (
            f"📦 GCS Upload Alert\n"
            f"Bucket: {bucket_name}\n"
            f"File: {file_name}\n"
            f"Type: {content_type}\n"
            f"Size: {size} bytes\n"
            f"Created: {time_created}\n"
            #f"Updated: {updated}\n"
            #f"Storage: {storage_class}"
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

        logging.info(f"✅ SMS sent! SID: {message.sid}")
    except Exception as e:
        logging.error(f"❌ Failed to send SMS: {str(e)}")
