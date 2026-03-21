import time
import os
from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob

ENV = os.getenv("ENV", "dev")
RUN_ID = str(int(time.time()))
PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"
BUCKET_NAME = "mlops-pipeline-01"

# Cloud Build trigger ID
TRIGGER_ID = "9fd79cf3-7464-4ed8-9290-523e3e88162e"

PIPELINE_ROOT = f"gs://{BUCKET_NAME}/monitoring-pipelines/{ENV}/{RUN_ID}"
DISPLAY_NAME = f"mlops-monitoring-{ENV}-{RUN_ID}"

FEATURES = [
    "job_id",
    "priority",
    "family_type",
    "overall_processing_time",
    "overall_waiting_time",
    "tardiness",
    "breaks",
]

PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "bucket_name": BUCKET_NAME,
    "env": ENV,
    "data_prefix": f"monitoring/{ENV}/new_data/",
    "feature_set": ",".join(FEATURES),
    "f1_threshold": 0.80,
    "trigger_id": TRIGGER_ID,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name=DISPLAY_NAME,
    template_path="monitor_pipeline.yaml",
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
    failure_policy="fast",
)

job.submit(experiment=f"mlops-monitoring-{ENV}")
job.wait()