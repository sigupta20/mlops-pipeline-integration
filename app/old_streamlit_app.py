import os
import streamlit as st
from app.model_loader import load_model_from_gcs
from app.predictor import Predictor

st.set_page_config(page_title="Manufacturing Breakdown Predictor")
st.title("Manufacturing Breakdown Predictor")

BUCKET_NAME = os.getenv("MODEL_BUCKET")
MODEL_GCS_PATH = os.getenv("MODEL_GCS_PATH")

@st.cache_resource
def load_predictor():
    model_path = load_model_from_gcs(BUCKET_NAME, MODEL_GCS_PATH)
    return Predictor(model_path)

predictor = load_predictor()
st.success("Model loaded successfully")

#  Streamlit web-ui form to select values
with st.form("prediction_form"):

    job_id = st.number_input("Job ID", min_value=0, step=1)
    priority = st.number_input("Priority", min_value=0, max_value=20, step=1)

    smd_stage = st.selectbox("SMD Stage", ["SMD_0", "SMD_1", "SMD_2", "SMD_3", "SMD_4"])
    processing_time_s1 = st.number_input("Processing Time S1", min_value=0.0)

    aoi_stage = st.selectbox("AOI Stage", ["AOI_0", "AOI_1", "AOI_2", "AOI_3", "AOI_4"])
    processing_time_s2 = st.number_input("Processing Time S2", min_value=0.0)

    ss_stage = st.selectbox("SS Stage", ["SS_0", "SS_1", "SS_2", "SS_3", "SS_4"])
    processing_time_s3 = st.number_input("Processing Time S3", min_value=0.0)

    cc_stage = st.selectbox("CC Stage", ["CC_0", "CC_1"])
    processing_time_s4 = st.number_input("Processing Time S4", min_value=0.0)

    overall_processing_time = st.number_input("Overall Processing Time", min_value=0.0)
    overall_waiting_time = st.number_input("Overall Waiting Time", min_value=0.0)
    tardiness = st.number_input("Tardiness", min_value=0.0)

    submitted = st.form_submit_button("Predict")

# Serving predictions
if submitted:

    # EXACT feature order used during training (26 features)
    instance = [
        int(job_id),
        int(priority),

        int(smd_stage == "SMD_0"),
        int(smd_stage == "SMD_1"),
        int(smd_stage == "SMD_2"),
        int(smd_stage == "SMD_3"),
        int(smd_stage == "SMD_4"),
        float(processing_time_s1),

        int(aoi_stage == "AOI_0"),
        int(aoi_stage == "AOI_1"),
        int(aoi_stage == "AOI_2"),
        int(aoi_stage == "AOI_3"),
        int(aoi_stage == "AOI_4"),
        float(processing_time_s2),

        int(ss_stage == "SS_0"),
        int(ss_stage == "SS_1"),
        int(ss_stage == "SS_2"),
        int(ss_stage == "SS_3"),
        int(ss_stage == "SS_4"),
        float(processing_time_s3),

        int(cc_stage == "CC_0"),
        int(cc_stage == "CC_1"),
        float(processing_time_s4),

        float(overall_processing_time),
        float(overall_waiting_time),
        float(tardiness),
    ]

    prediction = predictor.predict(instance)

    if prediction == 1:
        st.error("⚠️ Breakdown predicted")
    else:
        st.success("✅ No breakdown predicted")
