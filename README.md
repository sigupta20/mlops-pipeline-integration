# mlops_pipeline


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
gcloud iam service-accounts create gke-ml-sa

or 

gcloud iam service-accounts create gke-ml-sa \
    --project=$PROJECT_ID

## Grant GCS Read Access
gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:gke-ml-sa@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Kubernetes Cluster (GKE)
gcloud container clusters create ml-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --workload-pool=mlops-pipeline-01.svc.id.goog


gcloud container clusters get-credentials ml-cluster \
  --zone europe-west1-b \
  --project mlops-pipeline-01


kubectl create serviceaccount knn-inference-sa


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