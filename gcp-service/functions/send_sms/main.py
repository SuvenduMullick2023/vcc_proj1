import functions_framework
import os
import google.cloud.pubsub_v1
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def send_sms(request):
    """
    Cloud Function to send SMS via Twilio (HTTP trigger)
    Returns JSON response with operation details
    """
    try:
        from twilio.rest import Client
        
        request_json = request.get_json(silent=True)
        logger.info(f"SMS request data: {request.data}")

        if not request_json:
            return {"status": "error", "message": "No JSON payload"}, 400

        # Twilio credentials from environment
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_FROM_NUMBER']
        to_number = os.environ['SMS_RECIPIENT']

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=f"Network Update: {json.dumps(request_json)}",
            from_=from_number,
            to=to_number
        )

        return {
            "status": "success",
            "service": "sms",
            "message_sid": message.sid,
            "status_code": 200,
            "message": "SMS queued for delivery"
        }, 200

    except Exception as e:
        logger.error(f"SMS error: {str(e)}")
        return {
            "status": "error",
            "service": "sms",
            "message": str(e)
        }, 500