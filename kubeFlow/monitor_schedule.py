import os
from google.cloud import aiplatform

PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"
BUCKET_NAME = "mlops-pipeline-01"

ENV = "prod"
TRIGGER_ID = "9fd79cf3-7464-4ed8-9290-523e3e88162e"
PIPELINE_TEMPLATE = "monitor_pipeline.yaml"

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
    "feature_set": ",".join(FEATURES),
    "f1_threshold": 0.80,
    "trigger_id": TRIGGER_ID,
}

aiplatform.init(project=PROJECT_ID, location=REGION)

schedule = aiplatform.PipelineJobSchedule.create(
    display_name="mlops-monitoring-schedule-prod",
    template_path=PIPELINE_TEMPLATE,
    pipeline_root=f"gs://{BUCKET_NAME}/monitoring-pipelines/prod/scheduled",
    parameter_values=PIPELINE_PARAMS,
    cron="0 */12 * * *",
    max_concurrent_run_count=1,
)

print("Monitoring schedule created successfully!")
print(f"Schedule name: {schedule.resource_name}")