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
            "family_type": row["Family_type"],

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
def train_model_op(prepared_data: Input[Dataset], model: Output[Model], bucket_name: str, env: str, feature_set: str):
    import pandas as pd
    import joblib
    import os
    from google.cloud import storage
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.ensemble import BaggingClassifier

    features = [c.strip() for c in feature_set.split(",")]
    # Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"), usecols=features)

    # Target variable: breaks
    target = 'breaks'

    # Define features and separate target
    X = df.drop(target, axis=1)
    y = df[target]

    # Split into Training and Test dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Train model
    knn_model = KNeighborsClassifier(n_neighbors=5,metric="minkowski")
    knn_model.fit(X_train, y_train)

    # Predict using test dataset
    y_pred = knn_model.predict(X_test)

    # convert labels into binary format: [0,1]
    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average='binary')

    print(f'Accuracy for "breaks": {accuracy}')
    print(f'F1-Score for "breaks": {f1}')

    # Save model locally to be used in next stage
    os.makedirs(model.path, exist_ok=True)
    local_model_path = os.path.join(model.path, "model.joblib")
    joblib.dump(knn_model, local_model_path)
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
    feature_set: str,
    f1_threshold: float = 0.7,
) -> NamedTuple("Outputs", [("deploy_decision", str)]):
    import os
    import pandas as pd
    import joblib
    from sklearn.metrics import f1_score
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score


    features = [c.strip() for c in feature_set.split(",")]
    # Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"), usecols=features)

    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    # Split data into test and training data
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Load model
    load_model = joblib.load(os.path.join(model.path, "model.joblib"))

    # Predict using test dataset
    y_pred = load_model.predict(X_test)

    # convert labels into binary format: [0,1]
    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average='binary')

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("f1_score_binary", f1)
    # log feature info too
    metrics.log_metric("num_features", len([c.strip() for c in feature_set.split(",")]))
    metrics.metadata["feature_set"] = feature_set

    print(f'Accuracy for "breaks": {accuracy}')
    print(f'F1-Score for "breaks": {f1}')

    return ("true" if f1 >= f1_threshold else "false",)

# Publish artifacts component
@component(
    base_image="europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0"
)
def publish_artifacts_op(
    bucket_name: str,
    env: str,
    run_id: str,
    feature_set: str,
    raw_data: Input[Dataset],
    prepared_data: Input[Dataset],
    model: Input[Model],
    deploy_decision: str,
):
    import os
    import json
    from datetime import datetime, timezone
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    raw_path = os.path.join(raw_data.path, "raw_data.csv")
    prepared_path = os.path.join(prepared_data.path, "prepared_data.csv")
    model_path = os.path.join(model.path, "model.joblib")

    base = f"artifacts/{env}/latest"

    bucket.blob(f"{base}/raw_data.csv").upload_from_filename(raw_path)
    bucket.blob(f"{base}/prepared_data.csv").upload_from_filename(prepared_path)
    bucket.blob(f"{base}/model.joblib").upload_from_filename(model_path)

    metadata = {
        "env": env,
        "run_id": run_id,
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_set": feature_set,
        "deploy_decision": deploy_decision,
        "raw_data_gcs": f"gs://{bucket_name}/{base}/raw_data.csv",
        "prepared_data_gcs": f"gs://{bucket_name}/{base}/prepared_data.csv",
        "model_gcs": f"gs://{bucket_name}/{base}/model.joblib",
    }
    bucket.blob(f"{base}/metadata.json").upload_from_string(
        json.dumps(metadata, indent=2),
        content_type="application/json",
    )

    print(f"Published artifacts to gs://{bucket_name}/{base}/")

# Register model to Model Registry
@component(
    base_image='europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.0'
)
def register_model_op(
    project_id: str,
    location: str,
    model: Input[Model],
    display_name: str,
    feature_set: str, 
    run_id: str,
    model_resource: Output[Artifact],
):
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)
    print(f"Registering model from: {model.path}")
    uploaded_model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model.path,
        serving_container_image_uri="europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
        description=f"feature_set={feature_set}",
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
    model_display_name: str,
    f1_threshold: float,
    feature_set: str,
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
        env=env,
        feature_set=feature_set
    )
    train_task.set_caching_options(False)

    # Evaluate model
    evaluate_task = evaluate_model_op(
        model=train_task.outputs["model"],
        prepared_data=prepare_task.outputs["prepared_data"],
        f1_threshold=f1_threshold,
        feature_set=feature_set,
    )
    evaluate_task.set_caching_options(False)

    # Publish artifacts
    publish_task = publish_artifacts_op(
        bucket_name=bucket_name,
        env=env,
        run_id=run_id,
        feature_set=feature_set,
        raw_data=extract_task.outputs["raw_data"],
        prepared_data=prepare_task.outputs["prepared_data"],
        model=train_task.outputs["model"],
        deploy_decision=evaluate_task.outputs["deploy_decision"],
    )
    publish_task.set_caching_options(False)

    # Register model if evaluation passes
    with dsl.If(evaluate_task.outputs["deploy_decision"] == "true"):
        register_model_op(
            project_id=project_id,
            location=location,
            model=train_task.outputs["model"],
            display_name=model_display_name,
            feature_set=feature_set,
            run_id=run_id,
        )
