# vcc_proj1
# GCP Service Deployment Instructions

## Prerequisites

1.  Google Cloud SDK (gcloud CLI) installed and configured.
2.  Python 3.9+ installed.
3.  SendGrid API key (for email functionality).
4.  Replace placeholders in the code (project ID, workflow ID, etc.).

## Setup

1.  **Create a Cloud Storage Bucket:**

    ```bash
    gcloud storage buckets create gs://your-bucket-name
    ```

2.  **Create Pub/Sub Topics:**

    ```bash
    gcloud pubsub topics create sms-topic
    ```
    ```bash
    gcloud pubsub topics create email-topic
    ```

3.  **Deploy Cloud Workflow:**

    ```bash
    gcloud workflows deploy your-workflow-id --source workflow.yaml --location=us-central1
    ```

4.  **Deploy FastAPI as Cloud Run:**

    ```bash
    gcloud run deploy rest-api-handler --source=. --region=us-central1 --allow-unauthenticated
    ```

5.  **Deploy Cloud Functions:**

    ```bash
    gcloud functions deploy send_sms --runtime python39 --trigger-topic sms-topic --source=. --entry-point send_sms
    gcloud functions deploy send_email --runtime python39 --trigger-topic email-topic --source=. --entry-point send_email
    ```

6.  **Set Environment Variables:**

    * For Cloud Functions, use the gcloud CLI to set `GCP_PROJECT` and `SENDGRID_API_KEY`.
    * For Cloud Run, you can set environment variables during deployment or using the Cloud Run console.

## Running Locally (for development)

1.  Navigate to the `gcp-service` directory.
2.  Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  Run the FastAPI server:

    ```bash
    uvicorn main:app --reload
    ```

## Notes

* Replace all placeholders (e.g., `your-bucket-name`, `your-workflow-id`, email addresses, API keys).
* Add error handling and logging as needed.
* Ensure proper authentication and permissions.
* Customize the Cloud Workflow and Cloud Function logic to match your specific requirements.