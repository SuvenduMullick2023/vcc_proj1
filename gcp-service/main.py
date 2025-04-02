from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import functions_framework
import os
import google.cloud.pubsub_v1
from google.cloud import workflows_v1
import logging
import json

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        project_id = os.environ.get("GCP_PROJECT")
        workflow_id = "your-workflow-id"
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