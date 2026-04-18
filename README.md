# mlops_pipeline
gcloud config set project mlops-pipeline-01
gcloud auth application-default login
gcloud auth login

## Documentation links:
https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/agentic-adk-vertex#standard
https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
https://docs.cloud.google.com/vertex-ai/docs/pipelines/build-pipeline
https://docs.cloud.google.com/vertex-ai/docs/pipelines/introduction
https://console.cloud.google.com/artifacts/docker/cloud-builders/us/gcr.io
https://console.cloud.google.com/artifacts/docker/mlops-pipeline-01/europe-west3/mlops-images
https://docs.cloud.google.com/vertex-ai/docs/training/pre-built-containers#scikit-learn
https://docs.cloud.google.com/build/docs/build-config-file-schema

## STEP 5 – Build & Push Image to Artifact Registry
gcloud artifacts repositories create mlops-images \
    --repository-format=docker \
    --location=europe-west1

gcloud artifacts repositories describe ml-images \
    --location europe-west1 \
    --project=mlops-pipeline-01

gcloud auth configure-docker europe-west1-docker.pkg.dev

docker build -t knn-inference .

docker tag knn-inference \
  europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-inference:1.0

docker push europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-inference:1.0


## Create Service Account
gcloud iam service-accounts create mlops-sa

or 

gcloud iam service-accounts create mlops-sa \
    --project=$PROJECT_ID

## Grant GCS Read Access
gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:mlops-sa@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:mlops-sa@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:mlops-sa@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Kubernetes Cluster (GKE)

gcloud auth login
gcloud auth application-default login


gcloud container clusters create mlops-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --workload-pool=mlops-pipeline-01.svc.id.goog


gcloud container clusters get-credentials mlops-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01


kubectl create serviceaccount mlops-ksa


kubectl config current-context

kubectl get nodes


gcloud iam service-accounts add-iam-policy-binding \
  mlops-sa@mlops-pipeline-01.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:mlops-pipeline-01.svc.id.goog[default/mlops-ksa]"

kubectl annotate serviceaccount mlops-ksa \
  iam.gke.io/gcp-service-account=mlops-sa@mlops-pipeline-01.iam.gserviceaccount.com


kubectl describe serviceaccount mlops-ksa


## Delete the GKE cluster
gcloud container clusters delete mlops-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01


## apply deployment
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -l app=mlops-streamlit


## apply service
kubectl apply -f service.yaml
kubectl get svc mlops-svc // get external IP


## STEP 9 – Serve Predictions
curl http://34.52.178.179/health

curl -X POST http://EXTERNAL_IP/predict \
  -H "Content-Type: application/json" \
  -d '{
        "features": [1,2,3,4,5,6,7,8,9,10,
                     11,12,13,14,15,16,17,
                     100,5,0]
      }'

curl -X POST http://34.52.178.179/predict -H "Content-Type: application/json" \
  -d '{
        "features": [1,2,3,4,5,6,7,8,9,10,
                     11,12,13,14,15,16,17,
                     100,5,0]
      }'



## Vertex AI pipeline implementation steps

# 1. Enable API
gcloud services enable artifactregistry.googleapis.com

# 2. Create repo (if missing)
gcloud artifacts repositories create ml-images \
  --repository-format=docker \
  --location=europe-west1 \
  --project=mlops-pipeline-01

# 3. Authenticate Docker
gcloud auth configure-docker europe-west1-docker.pkg.dev

docker build -t europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-trainer:1.0 .
# 4. Push image
docker push europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-trainer:1.0

gcloud builds submit \
  --project mlops-pipeline-01 \
  --region europe-west1 \
  --tag europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-trainer:1.0



## cloud build commands:
gcloud builds submit   --config cloudbuild.yaml   --substitutions=_MODEL_URI=gs://mlops-pipeline-01-vertex-staging-europe-west1/vertex_ai_auto_staging/2026-01-13-19:31:19.157

gcloud builds submit   --config cloudbuild-deploy.yaml   --substitutions=_IMAGE_URI=europe-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-serving:7137cfa7-33c2-4718-9ccf-95269fda2f34 (Tag)

gcloud builds submit --config=cloudbuild.yaml .

gcloud builds submit --config=cloudbuild.yaml . &

## endpoints
to check endpoints:
gcloud ai endpoints list --region=europe-west1

if endpoints exists, check deployments:
gcloud ai endpoints describe ENDPOINT_ID \
  --region=europe-west1

create endpoints for the model:
gcloud ai endpoints create \
  --display-name=knn-endpoint-production \
  --region=europe-west1

deploy model to the endpoint:
gcloud ai endpoints deploy-model ENDPOINT_ID \
  --model=MODEL_ID \
  --display-name=knn-deployment-production \
  --machine-type=n1-standard-2 \
  --min-replica-count=1 \
  --max-replica-count=3 \
  --traffic-split=0=100 \
  --region=europe-west1


## deploy streamlit app
gcloud run deploy knn-streamlit \
  --image=europe-west1-docker.pkg.dev/PROJECT_ID/ml-images/knn-streamlit:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars MODEL_BUCKET=your-bucket-name,MODEL_GCS_PATH=dev/model/model.joblib

## Configure and Deploy SMTP notifier

https://docs.cloud.google.com/build/docs/configuring-notifications/configure-smtp

-- Enable APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  compute.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  --project=mlops-pipeline-01

-- Add SMTP secret in the secret manager

-- Grant the Cloud Run runtime service account access to the secret
gcloud secrets add-iam-policy-binding smtp-password \
  --member="serviceAccount:71707089683-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=mlops-pipeline-01

-- Grant Cloud Storage read access to the Cloud Run runtime service account
gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:71707089683-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"


-- upload the files
gcloud storage cp smtp-notifier.yaml gs://mlops-pipeline-01/smtp/smtp-notifier.yaml
gcloud storage cp smtp.html gs://mlops-pipeline-01/smtp/smtp.html

-- Deploy the SMTP notifier to Cloud Run
gcloud run deploy cloud-build-smtp-notifier \
  --image=us-east1-docker.pkg.dev/gcb-release/cloud-build-notifiers/smtp:latest \
  --no-allow-unauthenticated \
  --region=europe-west1 \
  --project=mlops-pipeline-01 \
  --update-env-vars=CONFIG_PATH=gs://mlops-pipeline-01/smtp/smtp-notifier.yaml,PROJECT_ID=mlops-pipeline-01

-- Create the Pub/Sub invoker service account
gcloud iam service-accounts create cloud-run-pubsub-invoker \
  --project=mlops-pipeline-01 \
  --display-name="Cloud Run Pub/Sub Invoker"

-- Allow that service account to invoke the Cloud Run service
gcloud run services add-iam-policy-binding cloud-build-smtp-notifier \
  --region=europe-west1 \
  --project=mlops-pipeline-01 \
  --member="serviceAccount:cloud-run-pubsub-invoker@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

-- Let Pub/Sub mint tokens for push auth
gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:service-71707089683@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"

-- Create the Cloud Build notifications topic
gcloud pubsub topics create cloud-builds \
  --project=mlops-pipeline-01

-- Get the Cloud Run service URL
gcloud run services describe cloud-build-smtp-notifier \
  --region=europe-west1 \
  --project=mlops-pipeline-01 \
  --format="value(status.url)"

-- Create the Pub/Sub push subscription
gcloud pubsub subscriptions create cloud-builds-smtp-sub \
  --project=mlops-pipeline-01 \
  --topic=cloud-builds \
  --push-endpoint=https://cloud-build-smtp-notifier-sygsyjbblq-ew.a.run.app \
  --push-auth-service-account=cloud-run-pubsub-invoker@mlops-pipeline-01.iam.gserviceaccount.com

-- Read service logs
gcloud run services logs read cloud-build-smtp-notifier \
  --region=europe-west1 \
  --project=mlops-pipeline-01 \
  --limit=100

-- delete resources
gcloud run services delete cloud-build-smtp-notifier \
  --region=europe-west1 \
  --project=mlops-pipeline-01

gcloud pubsub subscriptions delete cloud-builds-smtp-sub \
  --project=mlops-pipeline-01

gcloud pubsub topics delete cloud-builds \
  --project=mlops-pipeline-01

gcloud secrets delete smtp-password \
  --project=mlops-pipeline-01

gcloud iam service-accounts delete cloud-run-pubsub-invoker@mlops-pipeline-01.iam.gserviceaccount.com \
  --project=mlops-pipeline-01