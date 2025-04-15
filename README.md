# vcc_proj1 - Serverless email/SMS Application

# Instructions for GCP Service Deployment/Resource creation using Google Cloud UI.

## Prerequisites

1.  Google Cloud SDK (gcloud CLI) installed and configured.
2.  Python 3.10+ installed.
3.  SendGrid API key (for email functionality).
4.  Replace placeholders in the code (project ID, workflow ID, etc.).
5.  MySQL 8.0 instance on Google Cloud. Create a database with name **analysis**.

## Assumption

1. Files are uploaded to source buckets by a client application.
2. File containing **_eu** in name is considered from EU regions and all other files would be considered from non-EU region.

## Setup

1.  **Create a Cloud Storage Bucket:**

    ```bash
    gcloud storage buckets create gs://your-bucket-name
    ```
    Below buckets need to be created:
    
    ![image](https://github.com/user-attachments/assets/9b8c0578-8035-498a-aff8-bf512f6a7f5e)

    We have provide a sample script in workflows folder in our solution with function **create_bucket_if_not_exists** that would create buckets as part of automation. For some buckets, we created them from Google Cloud console UI.

3.  **Create Cloud Run Functions:**

    Below cloud run functions need to be created:

    ![image](https://github.com/user-attachments/assets/7429fc91-2512-4bdb-b957-247d79dc1374)

    The **main.py** and **requirements.txt** have been placed as per below paths:
    https://github.com/SuvenduMullick2023/vcc_proj1/tree/main/gcp-service/functions/file-aggregator
    https://github.com/SuvenduMullick2023/vcc_proj1/tree/main/gcp-service/functions/send_email
    https://github.com/SuvenduMullick2023/vcc_proj1/tree/main/gcp-service/functions/send_sms

    We need to replace <placeholders> in send_email and send_sms to enable notifications send functionality.

    We created cloud run functions using console and provided sample scripts in workflows:

    ![image](https://github.com/user-attachments/assets/f437ffef-13ce-4906-bafb-287a2beeb65f)

    We allowed internet access and added cloud storage trigger on our source bucket **user_uploaded_project_files**.

5.  **Cloud Scheduler**

    A Cloud Scheduler would be created with a schedule of 2 minutes as shown below:
    
    ![image](https://github.com/user-attachments/assets/69e42d95-f7ef-44a1-b7e3-43070e68bb22)

6.  **Grant Permissions**

    Provide following permissions to our default user running application workflow:

    ![image](https://github.com/user-attachments/assets/d571fe37-76c5-429b-b6a8-bab594af883d)
   
6.  **Deploy Cloud Workflow:**

    ```bash
    gcloud workflows deploy your-workflow-id --source workflow.yaml --location=us-central1
    ```

7.  **Deploy FastAPI as Cloud Run:**

    ```bash
    gcloud run deploy rest-api-handler --source=. --region=us-central1 --allow-unauthenticated
    ```

8.  **Deploy Cloud Functions:**

    ```bash
    gcloud functions deploy send_sms --runtime python39 --trigger-topic sms-topic --source=. --entry-point send_sms
    gcloud functions deploy send_email --runtime python39 --trigger-topic email-topic --source=. --entry-point send_email
    ```

9.  **Set Environment Variables:**

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
