import functions_framework
import os
import google.cloud.pubsub_v1
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def send_sms(cloud_event):
    """
    Cloud Function to send SMS messages via Pub/Sub.
    """
    try:
        message = json.loads(cloud_event.data.decode('utf-8'))
        logger.info(f"Received SMS message: {message}")

        # Use Pub/Sub to send the SMS message
        project_id = os.environ.get("GCP_PROJECT")
        topic_id = "sms-topic"  # Replace with your Pub/Sub topic ID

        publisher = google.cloud.pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)
        publisher.publish(topic_path, data=json.dumps(message).encode("utf-8"))
        logger.info("SMS message published to Pub/Sub.")

    except Exception as e:
        logger.error(f"Error sending SMS: {e}")