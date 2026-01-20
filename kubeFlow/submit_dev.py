import time
from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob

ENV = "dev"
RUN_ID = str(int(time.time()))
PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west3"
BUCKET_NAME = "mlops-pipeline-01"
PIPELINE_ROOT = f"gs://mlops-pipeline-01/pipelines/{ENV}/{RUN_ID}"
DISPLAY_NAME = f"mlops-training-{ENV}-{RUN_ID}"
TEMPLATE_PATH = "mlops_manufacturing_pipeline.yaml"



PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "env": ENV,
    "run_id": RUN_ID,
    "bucket_name": BUCKET_NAME,
    # "endpoint_display_name": "knn-endpoint-dev",
    "model_display_name": "mlops-model-dev",
    "f1_threshold": 0.80,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name=DISPLAY_NAME,
    template_path=TEMPLATE_PATH,
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
)

job.run(sync=True)
