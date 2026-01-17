from kfp.dsl import component, Dataset, Output, Input, Model

@component(
    base_image="python:3.10",
    packages_to_install=[
        "pandas",
        "scikit-learn",
        "joblib",
        "google-cloud-storage",
    ],
)
def train_knn_op(
    prepared_data: Input[Dataset],
    model: Output[Model],
    bucket_name: str,
):
    import pandas as pd
    import joblib
    import os
    from google.cloud import storage
    from sklearn.neighbors import KNeighborsClassifier

    # 1️⃣ Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"))
    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    # 2️⃣ Train model
    clf = KNeighborsClassifier(n_neighbors=5)
    clf.fit(X, y)

    # 3️⃣ Save model locally (Kubeflow artifact)
    os.makedirs(model.path, exist_ok=True)
    local_model_path = os.path.join(model.path, "model.joblib")
    joblib.dump(clf, local_model_path)

    print(f"Model saved locally at {local_model_path}")

    # 4️⃣ Upload model to GCS (Python SDK)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    gcs_blob_path = "dev/model/model.joblib"
    blob = bucket.blob(gcs_blob_path)
    blob.upload_from_filename(local_model_path)

    print(f"Model uploaded to gs://{bucket_name}/{gcs_blob_path}")
