from kfp import dsl, compiler
from kfp.dsl import component, Dataset, Input, Output
from typing import NamedTuple

BASE_IMAGE = "europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.1.0"


# Extract data component
@component(base_image=BASE_IMAGE)
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

    output_path = os.path.join(raw_data.path, "raw_data.csv")
    os.makedirs(raw_data.path, exist_ok=True)
    pd.concat(dfs, ignore_index=True).to_csv(output_path, index=False)


# Prepare data component
@component(base_image=BASE_IMAGE)
def prepare_data_op(raw_data: Input[Dataset], prepared_data: Output[Dataset]):
    import pandas as pd
    import os

    df = pd.read_csv(os.path.join(raw_data.path, "raw_data.csv"))

    prepared_rows = []
    for _, row in df.iterrows():
        prepared_rows.append({
            "job_id": row["ID"],
            "priority": row["Priority"],
            "family_type": row["Family_type"],
            "overall_processing_time": float(row["Overall_processing_time"]),
            "overall_waiting_time": float(row["Overall_waiting_time"]),
            "tardiness": float(row["Tardiness"]),
            "breaks": int(row["BREAKS"]),
        })

    output_path = os.path.join(prepared_data.path, "prepared_data.csv")
    os.makedirs(prepared_data.path, exist_ok=True)
    pd.DataFrame(prepared_rows).to_csv(output_path, index=False)

# Evaluate data component
@component(base_image=BASE_IMAGE)
def evaluate_data_op(
    bucket_name: str,
    env: str,
    prepared_data: Input[Dataset],
    feature_set: str,
    f1_threshold: float,
) -> NamedTuple("Outputs", [("retrain_decision", str), ("f1_score", float)]):
    import os
    import joblib
    import pandas as pd
    from google.cloud import storage
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score

    client = storage.Client()
    path = "/tmp/model.joblib"
    client.bucket(bucket_name).blob(f"artifacts/{env}/latest/model.joblib").download_to_filename(path)
    model = joblib.load(path)

    features = [c.strip() for c in feature_set.split(",")]
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"),usecols=features)

    X_test = df.drop(columns=["breaks"])
    y_test = df["breaks"]

    y_pred = model.predict(X_test)

    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    f1 = f1_score(y_test_binary, y_pred_binary, average="binary", zero_division=0)

    return ("true" if f1 < f1_threshold else "false", float(f1))

# Trigger New Run component
@component(base_image=BASE_IMAGE)
def trigger_new_run_op(
    project_id: str,
    location: str,
    f1_score: float,
    trigger_id: str,
):
    import subprocess

    print(f"F1 score {f1_score:.4f} is below threshold. Triggering Cloud Build.")

    cmd = [
        "gcloud",
        "builds",
        "triggers",
        "run",
        trigger_id,
        "--region",
        location,
        "--project",
        project_id,
    ]

    subprocess.run(cmd, check=True)
    print("Cloud Build trigger started successfully.")

@dsl.pipeline(
    name="mlops-monitoring-pipeline",
    description="Evaluate latest registered model on new labeled data and trigger retraining if degraded",
)
def monitoring_pipeline(
    project_id: str,
    location: str,
    bucket_name: str,
    env: str,
    feature_set: str,
    f1_threshold: float,
    trigger_id: str,
):
    model_display_name = f"mlops-model-{env}"

    extract_task = extract_data_op(bucket_name=bucket_name,)
    extract_task.set_caching_options(False)

    prepare_task = prepare_data_op(raw_data=extract_task.outputs["raw_data"],)
    prepare_task.set_caching_options(False)

    evaluate_task = evaluate_data_op(
        bucket_name=bucket_name,
        env=env,
        prepared_data=prepare_task.outputs["prepared_data"],
        feature_set=feature_set,
        f1_threshold=f1_threshold,
    )
    evaluate_task.set_caching_options(False)

    with dsl.If(evaluate_task.outputs["retrain_decision"] == "true"):
        trigger_task = trigger_new_run_op(
            project_id=project_id,
            location=location,
            f1_score=evaluate_task.outputs["f1_score"],
            trigger_id=trigger_id,
        )
        trigger_task.set_caching_options(False)

if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=monitoring_pipeline,
        package_path="monitor_pipeline.yaml",
    )
    print("Compiled monitoring pipeline to monitor_pipeline.yaml")