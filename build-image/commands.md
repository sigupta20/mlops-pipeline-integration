gcloud config set project mlops-pipeline-01

gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

gcloud artifacts repositories create mlops-build-image \
    --repository-format=docker \
    --location=europe-west3 \
    --description="Docker base image for MLOps pipelines"


gcloud auth configure-docker europe-west3-docker.pkg.dev

docker build -t mlops-build:1.0.0 .

docker tag mlops-build:v1 \
    europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build-image/mlops-build:1.0.0

docker push europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build-image/mlops-build:1.0.0


