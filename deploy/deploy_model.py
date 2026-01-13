from google.cloud import aiplatform
import os

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]
MODEL_ARTIFACT_URI = os.environ["MODEL_ARTIFACT_URI"]
SERVING_IMAGE_URI = os.environ["SERVING_IMAGE_URI"]
ENDPOINT_NAME = os.environ["ENDPOINT_NAME"]

aiplatform.init(project=PROJECT_ID, location=REGION)

print("Uploading model with serving container...")

model = aiplatform.Model.upload(
    display_name="knn-model-prod",
    artifact_uri=MODEL_ARTIFACT_URI,
    serving_container_image_uri=SERVING_IMAGE_URI,
    serving_container_predict_route="/predict",
    serving_container_health_route="/health",
)

print("Model uploaded:", model.resource_name)

endpoints = aiplatform.Endpoint.list(filter=f'display_name="{ENDPOINT_NAME}"')

if endpoints:
    endpoint = endpoints[0]
else:
    endpoint = aiplatform.Endpoint.create(display_name=ENDPOINT_NAME)

endpoint.deploy(
    model=model,
    deployed_model_display_name="knn-serving-v1",
    machine_type="n1-standard-4",
    traffic_percentage=100,
)

print("Deployment completed")
