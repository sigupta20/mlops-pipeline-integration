import time
import os
from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob

ENV = os.getenv("ENV", "dev")
PROJECT_ID = "mlops-241257"
REGION = "europe-west1"
BUCKET_NAME = "mlops-241257"

PIPELINE_ROOT = f"gs://{BUCKET_NAME}/pipelines/{ENV}"
DISPLAY_NAME = f"mlops-pipeline-{ENV}"
TEMPLATE_PATH = "pipeline.yaml"

# List of features
FEATURES = [
    "job_id",
    "priority",
    "family_type",
    # "smd_0","smd_1","smd_2","smd_3","smd_4","processing_time_s1",
    # "aoi_0","aoi_1","aoi_2","aoi_3","aoi_4","processing_time_s2",
    # "ss_0","ss_1","ss_2","ss_3","ss_4","processing_time_s3",
    # "cc_0","cc_1","processing_time_s4",
    "overall_processing_time",
    "overall_waiting_time",
    "tardiness",
    "breaks",
]


PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "env": ENV,
    "bucket_name": BUCKET_NAME,
    "model_display_name": f"mlops-model-{ENV}",
    "feature_set": ",".join(FEATURES),
    "f1_threshold": 0.80,
    "n_neighbors": 5,
    "p": 2,
    "metric": "minkowski",
    "sender_email": "siddharth.gupta.ovgu@gmail.com",
    "smtp_secret_name": "smtp-password",
    "recipient_email": "siddharth.gupta.ovgu@gmail.com",
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name=DISPLAY_NAME,
    template_path=TEMPLATE_PATH,
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
)

job.submit(experiment=f"mlops-pipeline-{ENV}")
job.wait()
