import time
from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob

ENV = "dev"
RUN_ID = str(int(time.time()))

PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"

PIPELINE_ROOT = f"gs://ad-manufacturing-data-bucket/pipelines/{ENV}/{RUN_ID}"

PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "env": ENV,
    "run_id": RUN_ID,
    "bucket_name": "ad-manufacturing-data-bucket",
    "endpoint_display_name": "knn-endpoint-dev",
    "model_display_name": "knn-model-dev",
    "f1_threshold": 0.80,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name=f"knn-training-{ENV}",
    template_path="manufacturing_knn_pipeline.yaml",
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
)

job.run(sync=False)
