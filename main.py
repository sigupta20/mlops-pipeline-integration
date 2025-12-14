import os
import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import storage

MODEL_PATH = "/models/model.joblib"
BUCKET_NAME = "ad-manufacturing-data-bucket"
BLOB_NAME = "model.joblib"

app = FastAPI()
model = None


class PredictionRequest(BaseModel):
    features: list[float]


@app.on_event("startup")
def load_model():
    global model

    if not os.path.exists(MODEL_PATH):
        os.makedirs("/models", exist_ok=True)

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(BLOB_NAME)
        blob.download_to_filename(MODEL_PATH)

    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictionRequest):
    data = np.array(request.features).reshape(1, -1)
    pred = model.predict(data)[0]
    return {"prediction": int(pred)}
