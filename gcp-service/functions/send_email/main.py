import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import storage

def send_email(event, context):
    # Fetch environment variables
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    recipient_email = os.environ.get("EMAIL_RECIPIENT")

    # Extract basic info from event
    file_name = event['name']
    bucket_name = event['bucket']

    # Check if it's a deletion
    is_deleted = 'timeDeleted' in event

    # Construct the message body
    if is_deleted:
        subject = f"🗑️ File Deleted from GCS Bucket"
        body = f"""
        ⚠️ A file was deleted from your Google Cloud Storage bucket.

        📁 Bucket: {bucket_name}
        ❌ File Name: {file_name}
        🕒 Deletion Time: {event.get('timeDeleted')}
        """
    else:
        # Not deleted: Get metadata
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.reload()

        subject = f"✅ File Uploaded to GCS Bucket"
        body = f"""
        A new file has been uploaded to your GCS bucket.

        📁 Bucket: {bucket_name}
        📄 File Name: {blob.name}
        🕒 Created: {blob.time_created}
        🕒 Updated: {blob.updated}
        📦 Content-Type: {blob.content_type}
        📏 Size: {blob.size} bytes
        🔐 MD5 Hash: {blob.md5_hash}
        🔖 CRC32C: {blob.crc32c}
        👤 Owner: {blob.owner.get('entity') if blob.owner else 'N/A'}
        🌍 Storage Class: {blob.storage_class}
        🏷️ Custom Metadata: {blob.metadata if blob.metadata else 'None'}
        """

    # Construct email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
