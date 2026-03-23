import os
import streamlit as st
from google.cloud import storage
from app.predictor import Predictor, FEATURE_COLUMNS

st.set_page_config(page_title="Manufacturing Anomaly Detection")
st.title("Manufacturing Anomaly Detection")

MODEL_BUCKET = os.getenv("MODEL_BUCKET")
MODEL_GCS_PATH = os.getenv("MODEL_GCS_PATH")


@st.cache_resource
def get_predictor():
    client = storage.Client()
    bucket = client.bucket(MODEL_BUCKET)
    blob = bucket.blob(MODEL_GCS_PATH)
    local_path = "/tmp/model.joblib"
    blob.download_to_filename(local_path)
    return Predictor(local_path)


predictor = get_predictor()
st.success("Model loaded successfully")

with st.form("prediction_form"):
    job_id = st.number_input("Job ID", min_value=0, step=1)
    priority = st.number_input("Priority", min_value=0, max_value=20, step=1)
    family_type = st.number_input("Family type", min_value=0, step=1)

    overall_processing_time = st.number_input("Overall Processing Time", min_value=0.0)
    overall_waiting_time = st.number_input("Overall Waiting Time", min_value=0.0)
    tardiness = st.number_input("Tardiness", min_value=0.0)

    submitted = st.form_submit_button("Predict")

if submitted:
    features = {
        "job_id": int(job_id),
        "priority": int(priority),
        "family_type": int(family_type),
        "overall_processing_time": float(overall_processing_time),
        "overall_waiting_time": float(overall_waiting_time),
        "tardiness": float(tardiness),
    }

    pred = predictor.predict(features)

    if pred == 1:
        st.error("⚠️ Breakdown predicted")
    else:
        st.success("✅ No breakdown predicted")