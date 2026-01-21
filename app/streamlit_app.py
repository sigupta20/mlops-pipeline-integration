import os
import streamlit as st
from app.model_loader import load_model_from_gcs
from app.predictor import Predictor


st.set_page_config(page_title="Manufacturing Breakdown Predictor")

st.title("🛠 Manufacturing Breakdown Predictor")
st.write("GOOGLE_APPLICATION_CREDENTIALS =", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

BUCKET_NAME = os.getenv("MODEL_BUCKET")
MODEL_GCS_PATH = os.getenv("MODEL_GCS_PATH")

@st.cache_resource
def load_predictor():
    model_path = load_model_from_gcs(BUCKET_NAME, MODEL_GCS_PATH)
    return Predictor(model_path)

predictor = load_predictor()
st.success("Model loaded successfully")

with st.form("prediction_form"):
    priority = st.number_input("Priority", 0, 5, 1)
    submitted = st.form_submit_button("Predict")

if submitted:
    features = {"priority": priority}
    prediction = predictor.predict(features)

    if prediction == 1:
        st.error("⚠️ Breakdown predicted")
    else:
        st.success("✅ No breakdown predicted")
