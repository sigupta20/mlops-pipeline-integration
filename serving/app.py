import joblib
import os
import numpy as np
from fastapi import FastAPI

app = FastAPI()

MODEL_PATH = os.environ.get("MODEL_PATH", "/model/model.joblib")

@app.on_event("startup")
def load_model():
    global model
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully")

@app.post("/predict")
def predict(features: list):
    """
    features: [[f1, f2, f3, ...]]
    """
    X = np.array(features)
    preds = model.predict(X)
    return {"predictions": preds.tolist()}
