import os
import logging
from twilio.rest import Client
import functions_framework

logging.basicConfig(level=logging.INFO)

@functions_framework.cloud_event
def send_sms(cloud_event):
    try:
        data = cloud_event.data
        event_type = cloud_event["type"]

        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")
        size = data.get("size", "N/A")
        time_created = data.get("timeCreated", "N/A")
        updated = data.get("updated", "N/A")

        # Determine event
        if "finalize" in event_type:
            body = (
                f"[UPLOAD] {file_name} in {bucket_name}\n"
                f"Size: {size} bytes\n"
                f"Time: {time_created}"
            )
        elif "delete" in event_type:
            body = (
                f"[DELETE] {file_name} removed from {bucket_name}\n"
                f"Time: {updated}"
            )
        else:
            body = (
                f"[UNKNOWN EVENT] {file_name} in {bucket_name}"
            )

        # Twilio credentials
        account_sid = "<account_id>"
        auth_token = "<auth_token>"
        from_number = "<from_number>"
        to_number = "<recipient_number>"

        # Send SMS
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )

        logging.info(f"SMS sent! SID: {message.sid}")
    except Exception as e:
        logging.error(f"Failed to send SMS: {str(e)}")