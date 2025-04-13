from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import functions_framework
import os
#import google.cloud.pubsub_v1
from google.cloud import workflows_v1, logging_v2, functions_v1
import logging
import json
import subprocess
import functions.send_email
import functions.send_sms

from google.cloud.workflows.executions_v1 import ExecutionsClient
from google.cloud.workflows.executions_v1.types import Execution 
from google.api_core.exceptions import GoogleAPICallError

from google.cloud import logging as gcp_logging
from google.cloud.logging_v2 import Client as GCPLoggingClient

# Initialize logger early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Add this initialization at the top level after imports
logging_client = None

def initialize_clients():
    global gcp_logger_client, functions_client
    try:
        # Initialize GCP logging client
        gcp_logger_client = GCPLoggingClient()
        
        # Initialize Cloud Functions client
        functions_client = functions_v1.CloudFunctionsServiceClient()
        
        logger.info("GCP clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Service initialization failed")

# Initialize after logger setup
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
        key_file = "/home/suvendu/Desktop/VCC/project-1-autoscale-gcp-vm-e4be10f24915.json"  # Update with the actual path
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
def create_bucket_if_not_exists(bucket_name, location="us-central1"):
    try:
        logging.info(f"Checking if bucket '{bucket_name}' exists...")
        subprocess.run(["gsutil", "ls", f"gs://{bucket_name}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info(f"Bucket '{bucket_name}' already exists.")
    except subprocess.CalledProcessError:
        logging.info(f"Bucket '{bucket_name}' does not exist. Creating in location '{location}'...")
        try:
            subprocess.run(["gsutil", "mb", "-l", location, f"gs://{bucket_name}"], check=True)
            logging.info(f"Bucket '{bucket_name}' created successfully in '{location}'.")
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


def deploy_cloud_function(name, source_dir, entry_point, trigger_event, trigger_resource, env_vars):
    try:
        logging.info(f"Deploying function '{name}'...")

        cmd = [
            "gcloud", "functions", "deploy", name,
            "--gen2",
            "--runtime=python310",
            "--region=us-central1",
            f"--source={source_dir}",
            f"--entry-point={entry_point}",
            f"--trigger-event={trigger_event}",
            f"--trigger-resource={trigger_resource}",
            "--allow-unauthenticated",
            "--service-account=222387947495-compute@developer.gserviceaccount.com"
        ]

        for var in env_vars:
            cmd.append("--set-env-vars")
            cmd.append(var)

        subprocess.run(cmd, check=True)
        logging.info(f"Function '{name}' deployed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to deploy cloud function '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Function deploy failed: {str(e)}")
    
def deploy_cloud_function__deletion_update(name, source_dir, entry_point, trigger_event, trigger_resource, env_vars):
    try:
        logging.info(f"Deploying function '{name}'...")

        cmd = [
            "gcloud", "functions", "deploy", name,
            "--gen2",
            "--runtime=python310",
            "--region=us-central1",
            f"--source={source_dir}",
            f"--entry-point={entry_point}",
            f"--trigger-event={trigger_event}",
            f"--trigger-resource={trigger_resource}",
            "--allow-unauthenticated",
            "--service-account=222387947495-compute@developer.gserviceaccount.com"
        ]

        for var in env_vars:
            cmd.append("--set-env-vars")
            cmd.append(var)

        subprocess.run(cmd, check=True)
        logging.info(f"Function '{name}' deployed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to deploy cloud function '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Function deploy failed: {str(e)}")    


def trigger_workflow(data: dict, project_id: str, workflow_id: str, location: str = "us-central1") -> str:
    """
    Triggers a Google Cloud Workflow with the given data input.
    
    Args:
        data (dict): The input data to send to the workflow.
        project_id (str): GCP project ID.
        workflow_id (str): ID of the deployed Cloud Workflow.
        location (str): Region of the workflow.

    Returns:
        str: Name of the triggered workflow execution.
    """
    try:
        logger.info(f"Triggering workflow '{workflow_id}' with data: {data}")
        client = ExecutionsClient()
        parent = client.workflow_path(project_id, location, workflow_id)

        execution = Execution(argument=json.dumps(data))
        response = client.create_execution(parent=parent, execution=execution)
        
        logger.info(f"Workflow execution started: {response.name}")
        return response.name
    except Exception as e:
        logger.error(f"Workflow triggering failed: {e}")
        raise
            
# Before running the FastAPI app:
#create_bucket_if_not_exists("gcp-vcc-m22aie218-bucket-v1")  # Replace with a unique name        
        
# Before running the FastAPI app:
#deploy_workflow_if_not_exists("m22aie218-vcc-v1", "workflow.yaml", "us-central1") # Replace with your values        

@app.get("/logs/email")
async def get_email_logs(limit: int = 10):
    """Retrieve email function logs from GCP"""
    try:
        if not gcp_logger_client:
            raise HTTPException(status_code=500, detail="GCP logging client not initialized")

        # Build GCP log filter
        log_filter = (
            f'resource.type="cloud_function" '
            f'resource.labels.function_name="send_email" '
            f'severity>=INFO'
        )

        # Get entries from GCP logging
        entries = gcp_logger_client.list_entries(
            filter_=log_filter,
            resource_names=[f"projects/{PROJECT_ID}"],
            page_size=limit
        )

        # Process GCP log entries
        logs = []
        for entry in entries:
            logs.append({
                "timestamp": entry.timestamp.isoformat(),
                "severity": entry.severity.name,
                "message": entry.text_payload
            })

        # Use standard logger for local logging
        logger.debug(f"Retrieved {len(logs)} GCP log entries")
        
        return {"logs": logs[-limit:]}

    except GoogleAPICallError as e:
        logger.error(f"GCP log retrieval failed: {str(e)}")
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
    create_bucket_if_not_exists("gcp-vcc-m22aie218-bucket-v1", location="us-central1")
    deploy_workflow_if_not_exists("m22aie218-vcc-v1", "workflow.yaml", "us-central1")
    
    '''trigger_workflow(
            data={"LTE": "L1800", "5G": "NR3600"},
            project_id="gcp-vcc-m22aie218-bucket-v1",
            workflow_id="m22aie218-vcc-v1",
            location="us-central1"
        )'''
    deploy_cloud_function(
        name="send_sms",
        source_dir="functions/send_sms",
        entry_point="send_sms",
        trigger_event="google.storage.object.finalize",
        trigger_resource="gcp-vcc-m22aie218-bucket-v1",
        env_vars=[
            f"TWILIO_ACCOUNT_SID={os.environ.get('TWILIO_ACCOUNT_SID')}",
            f"TWILIO_AUTH_TOKEN={os.environ.get('TWILIO_AUTH_TOKEN')}",
            f"TWILIO_FROM_NUMBER={os.environ.get('TWILIO_FROM_NUMBER')}",
            f"SMS_RECIPIENT={os.environ.get('SMS_RECIPIENT')}"
        ]
    )

    # Deploy send_email
    deploy_cloud_function(
        name="send_email",
        source_dir="functions/send_email",
        entry_point="send_email",
        trigger_event="google.storage.object.finalize",
        trigger_resource="gcp-vcc-m22aie218-bucket-v1",
        env_vars=[
            f"EMAIL_SENDER={os.environ.get('EMAIL_SENDER')}",
            f"EMAIL_PASSWORD={os.environ.get('EMAIL_PASSWORD')}",
            f"EMAIL_RECIPIENT={os.environ.get('EMAIL_RECIPIENT')}"
        ]
    )

    deploy_cloud_function(
        name="send_email_delete",
        source_dir="functions/send_email",
        entry_point="send_email",
        trigger_event="google.storage.object.delete",
        trigger_resource="gcp-vcc-m22aie218-bucket-v1",
        env_vars=[
            f"EMAIL_SENDER={os.environ.get('EMAIL_SENDER')}",
            f"EMAIL_PASSWORD={os.environ.get('EMAIL_PASSWORD')}",
            f"EMAIL_RECIPIENT={os.environ.get('EMAIL_RECIPIENT')}"
        ]
    )
    
    
       
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))