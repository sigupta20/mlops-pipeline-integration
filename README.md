# mlops_pipeline


## STEP 5 – Build & Push Image to Artifact Registry
- gcloud auth configure-docker europe-west1-docker.pkg.dev
- docker build -t knn-inference .
- docker tag knn-inference \
    europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-inference:1.0
- docker push europe-west1-docker.pkg.dev/mlops-pipeline-01/ml-images/knn-inference:1.0

## Create Service Account
- gcloud iam service-accounts create gke-ml-sa

## Grant GCS Read Access
- gcloud projects add-iam-policy-binding mlops-pipeline-01 \
  --member="serviceAccount:gke-ml-sa@mlops-pipeline-01.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

## apply deployment
kubectl apply -f deployment.yaml

## apply service
kubectl apply -f service.yaml

## Get IP
kubectl get svc knn-inference-service

## STEP 9 – Serve Predictions
curl http://EXTERNAL_IP/health

curl -X POST http://EXTERNAL_IP/predict \
  -H "Content-Type: application/json" \
  -d '{
        "features": [1,2,3,4,5,6,7,8,9,10,
                     11,12,13,14,15,16,17,
                     100,5,0]
      }'

