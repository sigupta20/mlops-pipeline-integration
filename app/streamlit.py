import os
import streamlit as st
from app.predictor import Predictor, FEATURE_COLUMNS

st.set_page_config(page_title="Manufacturing Breakdown Predictor")
st.title("Manufacturing Breakdown Predictor")

MODEL_PATH = os.getenv("MODEL_PATH", "/models/model.joblib")

@st.cache_resource
def get_predictor():
    return Predictor(MODEL_PATH)

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