from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import functions_framework
import os
import google.cloud.pubsub_v1
from google.cloud import workflows_v1
import logging
import json
import subprocess

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PROJECT_ID = "project-1-autoscale-gcp-vm"
ZONE = "us-central1-c"
MACHINE_TYPE = "e2-medium"
IMAGE_PROJECT = "ubuntu-os-cloud"  # Project containing Ubuntu images
IMAGE_FAMILY = "ubuntu-2004-lts"  # Image family for Ubuntu 20.04 LTS
def authenticate_gcloud():
    try:
        logger.info("Authenticating gcloud account...")
        key_file = "/home/suvendu/VCC/VCC_m22aie218_assignment_1/project-1-autoscale-gcp-vm-e4be10f24915.json"  # Update with the actual path
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
        subprocess.run(["gcloud", "auth", "activate-service-account", "--key-file", key_file], check=True)
        subprocess.run(["gcloud", "config", "set", "project", "project-1-autoscale-gcp-vm"], check=True)
        logger.info("Authentication successful.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to authenticate gcloud account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to authenticate gcloud account: {str(e)}")

# Authenticate gcloud before running the FastAPI app
authenticate_gcloud()

#1. Cloud Storage Bucket Creation
def create_bucket_if_not_exists(bucket_name):
    try:
        logging.info(f"Checking if bucket '{bucket_name}' exists...")
        subprocess.run(["gsutil", "ls", f"gs://{bucket_name}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"Bucket '{bucket_name}' already exists.")
    except subprocess.CalledProcessError:
        logging.info(f"Bucket '{bucket_name}' does not exist. Creating...")
        try:
            subprocess.run(["gsutil", "mb", f"gs://{bucket_name}"], check=True)
            logging.info(f"Bucket '{bucket_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create bucket '{bucket_name}': {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create bucket: {str(e)}")



def deploy_workflow_if_not_exists(workflow_id, workflow_file, location):
    try:
        logging.info(f"Checking if workflow '{workflow_id}' exists...")
        subprocess.run(["gcloud", "workflows", "describe", workflow_id, "--location", location], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"Workflow '{workflow_id}' already exists.")
    except subprocess.CalledProcessError:
        logging.info(f"Workflow '{workflow_id}' does not exist. Deploying...")
        try:
            subprocess.run(["gcloud", "workflows", "deploy", workflow_id, "--source", workflow_file, "--location", location], check=True)
            logging.info(f"Workflow '{workflow_id}' deployed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to deploy workflow '{workflow_id}': {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to deploy workflow: {str(e)}")
        
# Before running the FastAPI app:
create_bucket_if_not_exists("GCP-VCC-m22aie218-bucket")  # Replace with a unique name        
        
# Before running the FastAPI app:
deploy_workflow_if_not_exists("m22aie218-vcc-v1", "workflow.yaml", "us-central1") # Replace with your values        

@app.post("/process")
async def process_data(data: dict):
    """
    Handles data processing and triggers SMS/email workflows.
    """
    try:
        logger.info(f"Received data: {data}")

        # Simulate data storage in Cloud Storage (you'd use the GCP client library)
        # Example:
        # from google.cloud import storage
        # client = storage.Client()
        # bucket = client.bucket("your-bucket-name")
        # blob = bucket.blob("data.json")
        # blob.upload_from_string(json.dumps(data))

        # Trigger Cloud Workflow
        project_id = "project-1-autoscale-gcp-vm" #os.environ.get("GCP_PROJECT")
        workflow_id = "m22aie218-vcc-v1"
        location = "us-central1"  # Replace with your workflow location

        client = workflows_v1.WorkflowsClient()
        parent = client.workflow_path(project_id, location, workflow_id)
        response = client.run_workflow(parent=parent, argument=json.dumps(data))
        logger.info(f"Workflow run initiated: {response.name}")

        return JSONResponse({"message": "Processing started."})

    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# If running locally, start the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))