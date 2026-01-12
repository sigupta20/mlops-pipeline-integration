from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob
import time

PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"

import time

PIPELINE_ROOT = f"gs://ad-manufacturing-data-bucket/pipeline-root-{int(time.time())}"
PIPELINE_SPEC = "manufacturing_knn_pipeline.yaml"

PIPELINE_PARAMS = {
    "project_id": PROJECT_ID,
    "location": REGION,
    "bucket_name": "ad-manufacturing-data-bucket",
    "endpoint_display_name": "knn-endpoint-dev",
    "model_display_name": "knn-model-dev",
    "f1_threshold": 0.85,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

job = PipelineJob(
    display_name="manufacturing-knn-training-pipeline-dev",
    template_path=PIPELINE_SPEC,
    pipeline_root=PIPELINE_ROOT,
    parameter_values=PIPELINE_PARAMS,
    enable_caching=True,
)

job.run(sync=True)
# job.submit()
