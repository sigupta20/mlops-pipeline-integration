import time
import os
from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob

ENV = os.getenv("ENV", "dev")
RUN_ID = str(int(time.time()))
PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"
BUCKET_NAME = "mlops-pipeline-01"

PIPELINE_ROOT = f"gs://{BUCKET_NAME}/pipelines/{ENV}/{RUN_ID}"
DISPLAY_NAME = f"mlops-training-{ENV}-{RUN_ID}"
TEMPLATE_PATH = "mlops_manufacturing_pipeline.yaml"

# List of features
FEATURES = [
    "job_id",
    "priority",
    "family_type",
    # "smd_0",
    # "smd_1",
    # "smd_2",
    # "smd_3",
    # "smd_4",
    # "processing_time_s1",
    # "aoi_0",
    # "aoi_1",
    # "aoi_2",
    # "aoi_3",
    # "aoi_4",
    # "processing_time_s2",
    # "ss_0",
    # "ss_1",
    # "ss_2",
    # "ss_3",
    # "ss_4",
    # "processing_time_s3",
    # "cc_0",
    # "cc_1",
    # "processing_time_s4",
    "overall_processing_time",
    "overall_waiting_time",
    "tardiness",
    "breaks",
]

PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "env": ENV,
    "run_id": RUN_ID,
    "bucket_name": BUCKET_NAME,
    "model_display_name": f"mlops-model-{ENV}",
    "feature_set": ",".join(FEATURES),
    "f1_threshold": 0.80,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name=DISPLAY_NAME,
    template_path=TEMPLATE_PATH,
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
)

job.submit(experiment=f"mlops-manufacturing-{ENV}")
job.wait()
