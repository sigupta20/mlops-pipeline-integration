gcloud run deploy knn-streamlit \
  --image=europe-west1-docker.pkg.dev/PROJECT_ID/ml-images/knn-streamlit:latest \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars MODEL_BUCKET=your-bucket-name,MODEL_GCS_PATH=dev/model/model.joblib
