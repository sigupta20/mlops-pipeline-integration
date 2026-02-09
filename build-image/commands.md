gcloud config set project mlops-pipeline-01

gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

gcloud artifacts repositories create mlops-build \
    --repository-format=docker \
    --location=europe-west3 \
    --description="Docker base image for MLOps pipelines"


gcloud auth configure-docker europe-west3-docker.pkg.dev

docker build -t mlops-build:1.0.1 .

docker tag mlops-build:1.0.1 \
    europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.1

docker push europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.1

gcloud builds submit --tag europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.1

or
cd build-image
gcloud builds submit --config=cloudbuild.yaml .
