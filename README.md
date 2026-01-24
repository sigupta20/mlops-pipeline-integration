# mlops_pipeline
Configure project: gcloud config set project mlops-pipeline-01




## STEP 5 – Build & Push Image to Artifact Registry
gcloud artifacts repositories create ml-images \
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



gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_ID@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Kubernetes Cluster (GKE)
gcloud container clusters create ml-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --workload-pool=mlops-pipeline-01.svc.id.goog


gcloud container clusters get-credentials mlops-cluster \
  --zone europe-west3-b \
  --project mlops-pipeline-01


kubectl create serviceaccount mlops-serving-ksa


kubectl config current-context

kubectl get nodes



## Kubernetes Identity
kubectl create serviceaccount knn-inference-sa



kubectl annotate serviceaccount knn-inference-sa \
  iam.gke.io/gcp-service-account=gke-ml-sa@mlops-pipeline-01.iam.gserviceaccount.com

or 

kubectl annotate serviceaccount knn-inference-sa \
    iam.gke.io/gcp-service-account=gke-ml-sa@$PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts add-iam-policy-binding \
  gke-ml-sa@mlops-pipeline-01.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:mlops-pipeline-01.svc.id.goog:default/knn-inference-sa"

or

gcloud iam service-accounts add-iam-policy-binding gke-ml-sa@mlops-pipeline-01.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID.svc.id.goog[default/knn-inference-sa]"


## Delete the GKE cluster
gcloud container clusters delete ml-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01


## apply deployment
kubectl apply -f deployment.yaml

## apply service
kubectl apply -f service.yaml

## Get IP
kubectl get svc knn-inference-service

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


## Documentation links:
https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/agentic-adk-vertex#standard
https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
https://docs.cloud.google.com/vertex-ai/docs/pipelines/introduction


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


## MLOps Level 2: CI/CD pipeline automation
extract_data
   ↓
prepare_data
   ↓
train_knn
   ↓
offline_evaluate
   ↓
(if metrics pass)
   ↓
upload_model
   ↓
deploy_model_to_endpoint


## File structure
mlops-pipeline-integration/
│
├── pipelines/
│   ├── manufacturing_knn_pipeline.py     # Vertex AI pipeline DAG
│   ├── compile_pipeline.py               # Compile pipeline → YAML
│   └── README.md                          # Pipeline-level documentation
│
├── components/
│   ├── data/
│   │   ├── extract_data_component.py     # GCS → raw dataset
│   │   └── prepare_data_component.py     # raw → prepared dataset
│   │
│   ├── training/
│   │   └── train_knn_component.py        # Model training
│   │
│   ├── evaluation/
│   │   ├── evaluate_model_component.py   # Offline evaluation (pipeline gate)
│   │   └── online_evaluate_model_component.py  # Production monitoring
│   │
│   ├── deployment/
│   │   ├── upload_model_component.py     # Model Registry
│   │   └── deploy_endpoint_component.py  # Endpoint deployment
│   │
│   └── __init__.py
│
├── ci/
│   ├── cloudbuild.yaml                   # CI/CD pipeline
│   └── triggers.md                       # CI/CD trigger explanation
│
├── config/
│   ├── dev.yaml                          # Dev environment config
│   ├── prod.yaml                         # Prod environment config
│   └── base.yaml                         # Shared config
│
├── scripts/
│   ├── submit_pipeline.py                # Manual pipeline trigger (dev only)
│   └── trigger_retraining.py             # Trigger pipeline from monitoring
│
├── tests/
│   ├── components/
│   │   ├── test_extract_data.py
│   │   ├── test_prepare_data.py
│   │   ├── test_train_knn.py
│   │   └── test_evaluate_model.py
│   │
│   └── pipelines/
│       └── test_pipeline_compile.py
│
├── Dockerfile                            # Optional (if using custom images)
├── requirements.txt                     # Local dev dependencies
├── pyproject.toml                       # Optional modern Python config
├── .gcloudignore
├── .gitignore
└── README.md

## cloud build commands:
gcloud builds submit   --config cloudbuild.yaml   --substitutions=_MODEL_URI=gs://mlops-pipeline-01-vertex-staging-europe-west1/vertex_ai_auto_staging/2026-01-13-19:31:19.157

gcloud builds submit   --config cloudbuild-deploy.yaml   --substitutions=_IMAGE_URI=europe-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-serving:7137cfa7-33c2-4718-9ccf-95269fda2f34 (Tag)


## endpoints
to check endpoints:
gcloud ai endpoints list --region=europe-west1

if endpoints exists, check deployments:
gcloud ai endpoints describe ENDPOINT_ID \
  --region=europe-west1

create endpoints for the model:
gcloud ai endpoints create \
  --display-name=knn-endpoint-prod \
  --region=europe-west1

deploy model to the endpoint:
gcloud ai endpoints deploy-model ENDPOINT_ID \
  --model=MODEL_ID \
  --display-name=knn-deployment-prod \
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