import os
import streamlit as st
from google.cloud import storage
from app.predictor import Predictor, FEATURE_COLUMNS

# Configure Streamlit page settings and title
st.set_page_config(page_title="Manufacturing Machine Breakdown Predection")
st.title("Manufacturing Machine Breakdown Predection")

# Read model location from environment variables
MODEL_BUCKET = os.getenv("MODEL_BUCKET")
MODEL_GCS_PATH = os.getenv("MODEL_GCS_PATH")


@st.cache_resource
def get_predictor():
    # Create GCS client and access the model file in the bucket
    client = storage.Client()
    bucket = client.bucket(MODEL_BUCKET)
    blob = bucket.blob(MODEL_GCS_PATH)

    # Download the model locally for inference
    local_path = "/tmp/model.joblib"
    blob.download_to_filename(local_path)

    # Load and return the predictor object
    return Predictor(local_path)

# Load the predictor once and reuse it across app runs
predictor = get_predictor()
st.success("Model loaded successfully")

# Create input form for user feature values
with st.form("prediction_form"):
    job_id = st.number_input("Job ID", min_value=0, max_value=200, step=1)
    priority = st.number_input("Priority", min_value=0, max_value=20, step=1)
    family_type = st.number_input("Family type", min_value=0, max_value=40, step=1)

    overall_processing_time = st.number_input("Overall Processing Time", min_value=0)
    overall_waiting_time = st.number_input("Overall Waiting Time", min_value=0)
    tardiness = st.number_input("Tardiness", min_value=0)

    # Submit button to trigger prediction
    submitted = st.form_submit_button("Predict")

if submitted:
    # Collect user inputs into a feature dictionary
    features = {
        "job_id": int(job_id),
        "priority": int(priority),
        "family_type": int(family_type),
        "overall_processing_time": int(overall_processing_time),
        "overall_waiting_time": int(overall_waiting_time),
        "tardiness": int(tardiness),
    }

    # Generate prediction from the loaded model
    pred = predictor.predict(features)

    # Machine breakdown prediction
    if pred == 1:
        st.error("⚠️ Breakdown predicted")
    else:
        st.success("✅ Breakdown not predicted")