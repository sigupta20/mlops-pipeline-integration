from kfp import dsl
from kfp.dsl import component, Dataset, Input, Output, Model, Metrics, Artifact
from google.cloud import aiplatform
from typing import NamedTuple
import time


# Extract data component
@component(
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def extract_data_op(bucket_name: str, raw_data: Output[Dataset]):
    import pandas as pd
    from google.cloud import storage
    import io
    import os

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    dfs = []

    for blob in bucket.list_blobs():
        if blob.name.endswith("_breakdowns.csv"):
            df = pd.read_csv(io.BytesIO(blob.download_as_string()))
            if "BREAKS" in df.columns:
                dfs.append(df)

    if not dfs:
        raise RuntimeError("No valid CSV files found")

    # Merge all DataFrames into a single DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)
    os.makedirs(raw_data.path, exist_ok=True)
    output_path = os.path.join(raw_data.path, "raw_data.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"Raw data written to {output_path}")

# Prepare data component
@component(   
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def prepare_data_op(raw_data: Input[Dataset], prepared_data: Output[Dataset]):
    import pandas as pd
    import os

    # 1. Load raw data
    raw_data_path = os.path.join(raw_data.path, "raw_data.csv")
    df = pd.read_csv(raw_data_path)

    # 2. Row-wise feature engineering, _ means implies this value is not used
    prepared_rows = []
    for _, row in df.iterrows():
        first_stage  = row["First_stage"]
        second_stage = row["Second_stage"]
        third_stage  = row["Third_stage"]
        fourth_stage = row["Fourth_stage"]

        prepared_rows.append({
            # Identifiers / metadata
            "job_id": row["ID"],
            "priority": row["Priority"],

            # First stage (SMD)
            "smd_0": int(first_stage == "SMD_0"),
            "smd_1": int(first_stage == "SMD_1"),
            "smd_2": int(first_stage == "SMD_2"),
            "smd_3": int(first_stage == "SMD_3"),
            "smd_4": int(first_stage == "SMD_4"),
            "processing_time_s1": float(row["Processing_Time_S1"]),

            # Second stage (AOI)
            "aoi_0": int(second_stage == "AOI_0"),
            "aoi_1": int(second_stage == "AOI_1"),
            "aoi_2": int(second_stage == "AOI_2"),
            "aoi_3": int(second_stage == "AOI_3"),
            "aoi_4": int(second_stage == "AOI_4"),
            "processing_time_s2": float(row["Processing_Time_S2"]),

            # Third stage (SS)
            "ss_0": int(third_stage == "SS_0"),
            "ss_1": int(third_stage == "SS_1"),
            "ss_2": int(third_stage == "SS_2"),
            "ss_3": int(third_stage == "SS_3"),
            "ss_4": int(third_stage == "SS_4"),
            "processing_time_s3": float(row["Processing_Time_S3"]),

            # Fourth stage (CC)
            "cc_0": int(fourth_stage == "CC_0"),
            "cc_1": int(fourth_stage == "CC_1"),
            "processing_time_s4": float(row["Processing_Time_S4"]),
            
            "overall_processing_time": float(row["Overall_processing_time"]),
            "overall_waiting_time": float(row["Overall_waiting_time"]),
            "tardiness": float(row["Tardiness"]),
            "breaks": int(row["BREAKS"])
        })

    # 3. Save prepared dataset
    prepared_df = pd.DataFrame(prepared_rows)
    os.makedirs(prepared_data.path, exist_ok=True)
    output_path = os.path.join(prepared_data.path, "prepared_data.csv")
    prepared_df.to_csv(output_path, index=False)
    print("Prepared data written to:", output_path)

# Train model component
@component(
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def train_model_op(prepared_data: Input[Dataset], model: Output[Model], bucket_name: str, env: str):
    import pandas as pd
    import joblib
    import os
    from google.cloud import storage
    from sklearn.neighbors import KNeighborsClassifier

    # Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"))
    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    # Train model
    clf = KNeighborsClassifier(n_neighbors=5,metric="minkowski")
    clf.fit(X, y)

    # Save model locally (Kubeflow artifact)
    os.makedirs(model.path, exist_ok=True)
    local_model_path = os.path.join(model.path, "model.joblib")
    joblib.dump(clf, local_model_path)
    print(f"Model saved locally at {local_model_path}")

    # Upload model to GCS (Python SDK)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    gcs_blob_path = f"{env}/model/model.joblib"
    blob = bucket.blob(gcs_blob_path)
    blob.upload_from_filename(local_model_path)
    print(f"Model uploaded to gs://{bucket_name}/{gcs_blob_path}")

# Evaluate model component
@component(
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def evaluate_model_op(
    model: Input[Model],
    prepared_data: Input[Dataset],
    metrics: Output[Metrics],
    f1_threshold: float = 0.9,
) -> NamedTuple("Outputs", [("deploy_decision", str)]):
    import os
    import pandas as pd
    import joblib
    from sklearn.metrics import f1_score

    # Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"))
    X = df.drop("breaks", axis=1)
    y_true = df["breaks"]

    # Load model
    clf = joblib.load(os.path.join(model.path, "model.joblib"))

    # Predict
    y_pred = clf.predict(X)

    # Multiclass-safe F1
    f1 = f1_score(y_true, y_pred, average="weighted")
    metrics.log_metric("f1_score_weighted", f1)

    print(f"Weighted F1 score: {f1}")
    return ("true" if f1 >= f1_threshold else "false",)

# Register model to Model Registry
@component(
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def register_model_op(
    project_id: str,
    location: str,
    model: Input[Model],
    display_name: str,
    model_resource: Output[Artifact],
):
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)
    print(f"Registering model from: {model.path}")
    uploaded_model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model.path,
        serving_container_image_uri="europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
        sync=True,
    )
    with open(model_resource.path, "w") as f:
        f.write(uploaded_model.resource_name)

    print("Model registered:", uploaded_model.resource_name)


# Pipeline definition
@dsl.pipeline(name="mlops-manufacturing-pipeline", description="Train, evaluate and register ML model")

def mlops_manufacturing_pipeline(
    project_id: str,
    location: str,
    bucket_name: str,
    env: str,
    run_id: str,
    # endpoint_display_name: str = "mlops-endpoint",
    model_display_name: str,
    f1_threshold: float,
):

    # Extract data
    extract_task = extract_data_op(
        bucket_name=bucket_name
    )
    extract_task.set_caching_options(False)

    # Prepare data
    prepare_task = prepare_data_op(
        raw_data=extract_task.outputs["raw_data"]
    )
    prepare_task.set_caching_options(False)

    # Train model
    train_task = train_model_op(
        prepared_data=prepare_task.outputs["prepared_data"],
        bucket_name=bucket_name,
        env=env
    )
    train_task.set_caching_options(False)

    # Evaluate model
    evaluate_task = evaluate_model_op(
        model=train_task.outputs["model"],
        prepared_data=prepare_task.outputs["prepared_data"],
        f1_threshold=f1_threshold,
    )
    evaluate_task.set_caching_options(False)

    # Register model if evaluation passes
    with dsl.If(evaluate_task.outputs["deploy_decision"] == "true"):
        register_model_op(
            project_id=project_id,
            location=location,
            model=train_task.outputs["model"],
            display_name=model_display_name,
        )
