from kfp import dsl, compiler
from kfp.dsl import component, Dataset, Input, Output, Model, Metrics, Artifact
from typing import NamedTuple

BASE_IMAGE = "europe-west1-docker.pkg.dev/mlops-241257/mlops-build/mlops-build:1.3.0"

# Extract data component
@component(base_image=BASE_IMAGE)
def extract_data_op(bucket_name: str, env: str, raw_data: Output[Dataset]):
    import pandas as pd
    from google.cloud import storage
    import io
    import os

    # Create GCS client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Read CSV files from the bucket with machine breakdowns
    dfs = []
    for blob in bucket.list_blobs(prefix="data/"):
        if blob.name.endswith("_breakdowns.csv"):
            df = pd.read_csv(io.BytesIO(blob.download_as_string()))
            if "BREAKS" in df.columns:
                dfs.append(df)

    if not dfs:
        raise RuntimeError("No valid CSV files found")

    # Merge all dataframes and save as raw_data.csv
    os.makedirs(raw_data.path, exist_ok=True)
    output_path = os.path.join(raw_data.path, "raw_data.csv")
    pd.concat(dfs, ignore_index=True).to_csv(output_path, index=False)
    print(f"Raw data written to {output_path}")

    #Upload artifact for testing and model deployment
    base = f"artifacts/{env}/latest"
    bucket.blob(f"{base}/raw_data.csv").upload_from_filename(output_path)
    print(f"Raw data published to gs://{bucket_name}/{base}/raw_data.csv")


# Prepare data component
@component(base_image=BASE_IMAGE)
def prepare_data_op(bucket_name: str, env: str, raw_data: Input[Dataset], prepared_data: Output[Dataset]):
    import pandas as pd
    import os
    from google.cloud import storage

    # Read raw_data.csv and store in a DataFrame
    df = pd.read_csv(os.path.join(raw_data.path, "raw_data.csv"))

    # Row-wise feature engineering (one-hot-encoding), _ means implies this value is not used
    prepared_rows = []
    for _, row in df.iterrows():
        first_stage = row["First_stage"]
        second_stage = row["Second_stage"]
        third_stage = row["Third_stage"]
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
            "processing_time_s1": int(row["Processing_Time_S1"]),

            # Second stage (AOI)
            "aoi_0": int(second_stage == "AOI_0"),
            "aoi_1": int(second_stage == "AOI_1"),
            "aoi_2": int(second_stage == "AOI_2"),
            "aoi_3": int(second_stage == "AOI_3"),
            "aoi_4": int(second_stage == "AOI_4"),
            "processing_time_s2": int(row["Processing_Time_S2"]),

            # Third stage (SS)
            "ss_0": int(third_stage == "SS_0"),
            "ss_1": int(third_stage == "SS_1"),
            "ss_2": int(third_stage == "SS_2"),
            "ss_3": int(third_stage == "SS_3"),
            "ss_4": int(third_stage == "SS_4"),
            "processing_time_s3": int(row["Processing_Time_S3"]),

            # Fourth stage (CC)
            "cc_0": int(fourth_stage == "CC_0"),
            "cc_1": int(fourth_stage == "CC_1"),
            "processing_time_s4": int(row["Processing_Time_S4"]),

            "overall_processing_time": int(row["Overall_processing_time"]),
            "overall_waiting_time": int(row["Overall_waiting_time"]),
            "tardiness": int(row["Tardiness"]),
            "breaks": int(row["BREAKS"]),
        })

    # Save prepared dataset into prepared_data.csv
    output_path = os.path.join(prepared_data.path, "prepared_data.csv")
    os.makedirs(prepared_data.path, exist_ok=True)
    pd.DataFrame(prepared_rows).to_csv(output_path, index=False)
    print(f"Prepared data written to: {output_path}")

    #Upload artifact for testing and model deployment
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    base = f"artifacts/{env}/latest"
    bucket.blob(f"{base}/prepared_data.csv").upload_from_filename(output_path)
    print(f"Prepared data published to gs://{bucket_name}/{base}/prepared_data.csv")


# Train model component
@component(base_image=BASE_IMAGE)
def train_model_op(
    bucket_name: str, env: str,prepared_data: Input[Dataset], model: Output[Model],
    feature_set: str, n_neighbors: int,metric: str, p: int,
):
    import pandas as pd
    import joblib
    import os
    from google.cloud import storage
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    
    # Read features from the list
    features = [c.strip() for c in feature_set.split(",")]

    # Read prepared_data.csv and store in a DataFrame
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"), usecols=features)

    # Target attribute: breaks
    target = "breaks"

    # Define features and target attribute
    X = df.drop(columns=[target])
    y = df[target]

    # Split into Training and Test dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Train model
    knn_model = KNeighborsClassifier(n_neighbors=n_neighbors,metric=metric,p=p)
    knn_model.fit(X_train, y_train)

    # Predict using test dataset
    y_pred = knn_model.predict(X_test)

    # convert labels into binary format: [0,1]
    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average="binary")

    print(f"Accuracy: {accuracy}")
    print(f"F1 (binary): {f1}")
    print(f"Hyperparameters: n_neighbors={n_neighbors}, metric={metric}, p={p}")
    print(f"Features Set: {features}")

    # Save model locally to be used in next stage
    os.makedirs(model.path, exist_ok=True)
    model_path = os.path.join(model.path, "model.joblib")
    joblib.dump(knn_model, model_path)
    print(f"Model saved at {model_path}")

    #Upload artifact for testing and model deployment
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    base = f"artifacts/{env}/latest"
    bucket.blob(f"{base}/model.joblib").upload_from_filename(model_path)
    print(f"Model published to gs://{bucket_name}/{base}/model.joblib")


# Evaluate model component
@component(base_image=BASE_IMAGE)
def evaluate_model_op(
    bucket_name: str,model: Input[Model],prepared_data: Input[Dataset],metrics: Output[Metrics],
    feature_set: str,f1_threshold: float,env: str,
    sender_email: str,recipient_email: str,
    project_id: str,smtp_secret_name: str,
) -> NamedTuple("Outputs", [("deploy_decision", str),("accuracy", float),("f1_score", float),]):

    import os
    import json
    import pandas as pd
    import joblib
    from datetime import datetime
    from google.cloud import storage, secretmanager
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    import smtplib
    from email.mime.text import MIMEText

    features = [c.strip() for c in feature_set.split(",")]

    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"), usecols=features)

    X = df.drop(columns=["breaks"])
    y = df["breaks"]

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Load model from previous stage and predict using test dataset
    loaded_model = joblib.load(os.path.join(model.path, "model.joblib"))
    y_pred = loaded_model.predict(X_test)

    # convert labels into binary format: [0,1]
    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average="binary")

    # Log pipeline metrics as metadata
    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("f1", f1)
    metrics.log_metric("num_features", X.shape[1])
    metrics.metadata["environment"] = env
    metrics.metadata["features"] = feature_set
    metrics.metadata["model_type"] = "knn"

    deploy_decision = "true" if f1 >= f1_threshold else "false"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    base = f"artifacts/{env}/latest"

    metadata = {
        "Environment": env,
        "Published_At": datetime.now().isoformat(),
        "Features": feature_set,
        "Deploy_Decision": deploy_decision,
        "Accuracy": accuracy,
        "F1": f1,
    }
    bucket.blob(f"{base}/metadata.json").upload_from_string(
        json.dumps(metadata, indent=2),
        content_type="application/json",
    )
    print(f"Metadata published to gs://{bucket_name}/{base}/metadata.json")

    # Pipeline will fail with error if threshold below 90%
    if f1 < f1_threshold:
        sm_client = secretmanager.SecretManagerServiceClient()
        secret_path = (f"projects/{project_id}/secrets/{smtp_secret_name}/versions/latest")
        response = sm_client.access_secret_version(request={"name": secret_path})
        sender_password = response.payload.data.decode("UTF-8")
        subject = f"[{env}] MLOps Pipeline Alert - F1 score below threshold"
        body = f"""
        F1 score dropped below threshold.<br><br>
        <b>Environment:</b> {env}<br>
        <b>F1:</b> {f1:.4f}<br>
        <b>Threshold:</b> {f1_threshold:.4f}
        """        

        message = MIMEText(body, "html")
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print(f"Alert email sent to {recipient_email}")

        raise ValueError(
            f"Model rejected: f1_score_binary={f1} is below threshold={f1_threshold}"
        )

    return (deploy_decision, accuracy, f1)


# Register model to Model Registry
@component(base_image=BASE_IMAGE)
def register_model_op(
    project_id: str,location: str,
    model: Input[Model],model_resource: Output[Artifact],
    display_name: str,feature_set: str,env: str,
    ):
    import json
    from google.cloud import aiplatform

    # Initialize Vertex AI client
    aiplatform.init(project=project_id, location=location,staging_bucket=f"gs://{project_id}")

    # Format env value so it can be used as a valid label
    env_label = env.lower().replace("_", "-")[:63]

    # Verify whether a model with the same display name already exists
    models = aiplatform.Model.list(
        filter=f'display_name="{display_name}"',
        order_by="create_time desc",
    )
    # Use latest existing model as parent to create a new version
    parent_model = models[0].resource_name if models else None

    # Print basic registration details for logging
    print(f"Registering model from: {model.path}")
    print(f"Display name: {display_name}")
    print(f"Parent model: {parent_model or 'None (first version)'}")

    # Upload model artifact to Vertex AI Model Registry
    uploaded_model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model.path,
        serving_container_image_uri="europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
        description=f"env={env}; feature_set={feature_set}",
        labels={
            "env": env_label,
            "model_type": "knn",
        },
        parent_model=parent_model,
        sync=True,
    )

    # Store important model registration details as metadata
    metadata = {
        "vertex_model_resource_name": uploaded_model.resource_name,
        "display_name": display_name,
        "env": env,
        "feature_set": feature_set,
        "artifact_uri": model.path,
        "parent_model": parent_model,
    }

    # Write metadata to the output artifact file
    with open(model_resource.path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Attach metadata to the output artifact for pipeline tracking
    model_resource.metadata.update(metadata)
    print(f"Model registered: {uploaded_model.resource_name}")


# Pipeline definition
@dsl.pipeline(name="mlops-pipeline", description="Train, evaluate and register ML model")
def pipeline(
    project_id: str,
    location: str,
    bucket_name: str,
    env: str,
    model_display_name: str,
    f1_threshold: float,
    feature_set: str,
    n_neighbors: int,
    p: int,
    metric: str,
    sender_email: str,
    smtp_secret_name: str,
    recipient_email: str,
):
    extract_task = extract_data_op(bucket_name=bucket_name, env=env)
    extract_task.set_caching_options(False)

    prepare_task = prepare_data_op(
        bucket_name=bucket_name,
        env=env,
        raw_data=extract_task.outputs["raw_data"],
    )
    prepare_task.set_caching_options(False)

    train_task = train_model_op(
        bucket_name=bucket_name,
        env=env,
        prepared_data=prepare_task.outputs["prepared_data"],
        feature_set=feature_set,
        n_neighbors=n_neighbors,
        p=p,
        metric=metric,
    )
    train_task.set_caching_options(False)

    evaluate_task = evaluate_model_op(
        bucket_name=bucket_name,
        model=train_task.outputs["model"],
        prepared_data=prepare_task.outputs["prepared_data"],
        feature_set=feature_set,
        f1_threshold=f1_threshold,
        env=env,
        sender_email=sender_email,
        smtp_secret_name=smtp_secret_name,
        project_id=project_id,
        recipient_email=recipient_email,
    )
    evaluate_task.set_caching_options(False)

    with dsl.If(evaluate_task.outputs["deploy_decision"] == "true"):
        register_task = register_model_op(
            project_id=project_id,
            location=location,
            model=train_task.outputs["model"],
            display_name=model_display_name,
            feature_set=feature_set,
            env=env,
        )
        register_task.set_caching_options(False)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path="pipeline.yaml",
    )
    print("Compiled pipeline to pipeline.yaml")