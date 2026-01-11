from google.cloud import aiplatform
from google.cloud.aiplatform.pipeline_jobs import PipelineJob
from datetime import datetime

PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"
PIPELINE_JSON = "manufacturing_knn_pipeline.json"

def trigger_retraining(reason: str):
    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
    )

    job = PipelineJob(
        display_name=f"knn-retraining-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        template_path=PIPELINE_JSON,
        parameter_values={
            "project_id": PROJECT_ID,
            "location": REGION,
            "bucket_name": "ad-manufacturing-data-bucket",
            "endpoint_display_name": "knn-endpoint-prod",
            "model_display_name": "knn-model-prod",
            "f1_threshold": 0.9,
        },
        enable_caching=False,  # retraining should not be cached
    )

    job.run(sync=False)
    print(f"Retraining triggered. Reason: {reason}")


if __name__ == "__main__":
    trigger_retraining(reason="manual_test")
