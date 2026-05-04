gcloud config set project mlops-241257

gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

gcloud artifacts repositories create mlops-build \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Docker base image for MLOps pipelines"


gcloud auth configure-docker europe-west1-docker.pkg.dev

docker build -t mlops-build:1.3.0 .

docker tag mlops-build:1.3.0 \
    europe-west1-docker.pkg.dev/mlops-241257/mlops-build/mlops-build:1.3.0

docker push europe-west1-docker.pkg.dev/mlops-241257/mlops-build/mlops-build:1.3.0

gcloud builds submit --tag europe-west1-docker.pkg.dev/mlops-241257/mlops-build/mlops-build:1.3.0

or
cd build-image
gcloud builds submit --config=cloudbuild.yaml .
