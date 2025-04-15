import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import storage
import functions_framework

@functions_framework.cloud_event
def send_email(cloud_event):
    """Triggered by file upload or deletion in GCS"""
    try:
        data = cloud_event.data
        event_type = cloud_event["type"]  # Check the type of event

        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")
        content_type = data.get("contentType", "N/A")
        size = data.get("size", "N/A")
        time_created = data.get("timeCreated", "N/A")
        updated = data.get("updated", "N/A")
        storage_class = data.get("storageClass", "N/A")

        # Determine if it's an upload or delete event
        if "finalize" in event_type:
            subject = f"File Uploaded to GCS: {file_name}"
            body = (
                f"A new file has been uploaded to GCS bucket '{bucket_name}'.\n\n"
                f"- Name: {file_name}\n"
                f"- Type: {content_type}\n"
                f"- Size: {size} bytes\n"
                f"- Created: {time_created}\n"
                f"- Updated: {updated}\n"
                f"- Storage Class: {storage_class}"
            )
        elif "delete" in event_type:
            subject = f"File Deleted from GCS: {file_name}"
            body = (
                f"A file has been deleted from GCS bucket '{bucket_name}'.\n\n"
                f"- Name: {file_name}\n"
                f"- Deletion Time: {updated}"
            )
        else:
            subject = "GCS File Change Notification"
            body = f"A file change occurred in bucket '{bucket_name}': {file_name}"

        # Email credentials
        sender_email = "<sender_email>"
        sender_password = "<sender_password>"
        recipient_email = "<recipient_address>"

        # Compose the email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send the email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")