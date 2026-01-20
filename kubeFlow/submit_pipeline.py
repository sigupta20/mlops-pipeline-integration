from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob
import time

PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west3"

PIPELINE_ROOT = f"gs://mlops-pipeline-01/pipeline-root-{int(time.time())}"
PIPELINE_SPEC = "mlops_manufacturing_pipeline.yaml"

PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "bucket_name": "mlops-pipeline-01",
    "model_display_name": "knn-model-dev",
    "f1_threshold": 0.85,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name="manufacturing-knn-training-pipeline-dev",
    template_path=PIPELINE_SPEC,
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
    enable_caching=False,
)

job.run(sync=True)
