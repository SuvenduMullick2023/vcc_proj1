import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import storage
import functions_framework

@functions_framework.cloud_event
def send_email(cloud_event):
    """Triggered by file upload to GCS"""
    try:
        data = cloud_event.data
        file_name = data.get("name", "N/A")
        bucket_name = data.get("bucket", "N/A")
        content_type = data.get("contentType", "N/A")
        size = data.get("size", "N/A")
        time_created = data.get("timeCreated", "N/A")
        updated = data.get("updated", "N/A")
        storage_class = data.get("storageClass", "N/A")

        # Compose the email content
        subject = "📁 File Uploaded to GCS Bucket"
        body = (
            f"A new file has been uploaded to GCS bucket '{bucket_name}'.\n\n"
            f"🔹 Name: {file_name}\n"
            f"🔹 Type: {content_type}\n"
            f"🔹 Size: {size} bytes\n"
            f"🔹 Created: {time_created}\n"
            f"🔹 Updated: {updated}\n"
            f"🔹 Storage Class: {storage_class}"
        )

        # Environment variables
        sender_email = os.environ.get("EMAIL_SENDER")
        sender_password = os.environ.get("EMAIL_PASSWORD")
        recipient_email = os.environ.get("EMAIL_RECIPIENT")

        # Create email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
