from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import functions_framework
import os
import google.cloud.pubsub_v1
from google.cloud import workflows_v1, logging_v2, functions_v1
import logging
import json
import subprocess
import send_email
from google.cloud.workflows.executions_v1 import ExecutionsClient
from google.cloud.workflows.executions_v1.types import Execution 
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import logging_v2

# Add this initialization at the top level after imports
logging_client = None

def initialize_clients():
    global logging_client, functions_client
    try:
        logging_client = logging_v2.LoggingServiceClient()
        functions_client = functions_v1.CloudFunctionsServiceClient()
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Service initialization failed")
# Add this before your FastAPI endpoints
initialize_clients()
 
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
#create_bucket_if_not_exists("gcp-vcc-m22aie218-bucket-v1")  # Replace with a unique name        
        
# Before running the FastAPI app:
#deploy_workflow_if_not_exists("m22aie218-vcc-v1", "workflow.yaml", "us-central1") # Replace with your values        

@app.get("/logs/email")
async def get_email_logs(limit: int = 10):
    """Retrieve email function logs"""
    try:
        if not logging_client:
            raise HTTPException(status_code=500, detail="Logging client not initialized")
            
        log_filter = (
            f'resource.type="cloud_function" '
            f'resource.labels.function_name="send_email" '
            f'severity>=INFO'
        )

        logs = []
        entries = logging_client.list_log__entries(
            request={
                "resource_names": [f"projects/{PROJECT_ID}"],
                "filter": log_filter,
                "page_size": limit
            }
        )
        
        for entry in entries:
            logs.append({
                "timestamp": entry.timestamp.isoformat(),
                "severity": entry.severity.name,
                "message": entry.text_payload
            })

        return {"logs": logs[-limit:]}

    except GoogleAPICallError as e:
        logger.error(f"Log retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")


@app.post("/manage-permissions/email")
async def configure_email_permissions(public_access: bool = True):
    """Programmatically manage email function permissions"""
    try:
        function_path = functions_client.cloud_function_path(
            PROJECT_ID,
            'us-central1',
            'send_email'
        )

        policy = functions_client.get_iam_policy(resource=function_path)
        member = "allUsers"
        role = "roles/cloudfunctions.invoker"
        
        if public_access:
            binding = next((b for b in policy.bindings if b.role == role), None)
            if not binding:
                binding = functions_v1.Policy.Binding(role=role, members=[])
                policy.bindings.append(binding)
            if member not in binding.members:
                binding.members.append(member)
        else:
            for binding in policy.bindings:
                if binding.role == role and member in binding.members:
                    binding.members.remove(member)

        functions_client.set_iam_policy(
            resource=function_path,
            policy=policy
        )

        return {"status": "success", "public_access": public_access}

    except GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Permission update failed: {str(e)}") 
       
@app.get("/logs/sms")
async def get_sms_logs(limit: int = 10):
    """Retrieve SMS function logs programmatically"""
    try:
        log_filter = (
            f'resource.type="cloud_function" '
            f'resource.labels.function_name="send_sms" '
            f'severity>=INFO'
        )

        logs = []
        for entry in logging_client.list_log_entries(
            resource_names=[f"projects/{PROJECT_ID}"],
            filter_=log_filter,
            page_size=limit
        ):
            logs.append({
                "timestamp": entry.timestamp.isoformat(),
                "severity": entry.severity.name,
                "message": entry.text_payload
            })

        return {"logs": logs[-limit:]}

    except GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")
    
@app.post("/process")
async def process_data(data: dict):
    """
    Handles data processing and triggers SMS/email workflows.
    """
    try:
        logger.info(f"Received data: {data}")

        # Trigger Cloud Workflow
        project_id = "project-1-autoscale-gcp-vm"
        workflow_id = "m22aie218-vcc-v1"
        location = "us-central1"

        # Use ExecutionsClient instead of WorkflowsClient
        client = ExecutionsClient()
        parent = client.workflow_path(project_id, location, workflow_id)
        
        # Create execution with input data
        execution = Execution(argument=json.dumps(data))
        response = client.create_execution(
            parent=parent,
            execution=execution
        )
        
        logger.info(f"Workflow execution started: {response.name}")
        return JSONResponse({"message": "Processing started."})

    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# If running locally, start the FastAPI server
if __name__ == "__main__":
    authenticate_gcloud()
    create_bucket_if_not_exists("gcp-vcc-m22aie218-bucket-v1")
    deploy_workflow_if_not_exists("m22aie218-vcc-v1", "workflow.yaml", "us-central1")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))