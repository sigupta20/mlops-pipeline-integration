import os
import io
import numpy as np
import pandas as pd
import joblib
from google.cloud import storage


BUCKET = "mlops-pipeline-01"
ENV = os.getenv("ENV", "dev")

BASE = f"artifacts/{ENV}/latest"
RAW_DATA_BLOB = f"{BASE}/raw_data.csv"
PREPARED_DATA_BLOB = f"{BASE}/prepared_data.csv"
MODEL_BLOB = f"{BASE}/model.joblib"


EXPECTED_PREPARED_COLS = [
    "job_id",
    "priority",
    "family_type",
    # "smd_0", "smd_1", "smd_2", "smd_3", "smd_4",
    # "processing_time_s1",
    # "aoi_0", "aoi_1", "aoi_2", "aoi_3", "aoi_4",
    # "processing_time_s2",
    # "ss_0", "ss_1", "ss_2", "ss_3", "ss_4",
    # "processing_time_s3",
    # "cc_0", "cc_1",
    # "processing_time_s4",
    "overall_processing_time",
    "overall_waiting_time",
    "tardiness",
    "breaks",
]


def _gcs_client():
    return storage.Client()


def _download_bytes(bucket: str, blob_path: str) -> bytes:
    client = _gcs_client()
    b = client.bucket(bucket)
    blob = b.blob(blob_path)
    if not blob.exists():
        raise FileNotFoundError(f"Blob not found: gs://{bucket}/{blob_path}")
    return blob.download_as_bytes()


def _read_csv_from_gcs(bucket: str, blob_path: str) -> pd.DataFrame:
    data = _download_bytes(bucket, blob_path)
    return pd.read_csv(io.BytesIO(data))


def _download_model_from_gcs(bucket: str, blob_path: str, local_path: str) -> str:
    client = _gcs_client()
    b = client.bucket(bucket)
    blob = b.blob(blob_path)
    if not blob.exists():
        raise FileNotFoundError(f"Model not found: gs://{bucket}/{blob_path}")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    return local_path


def test_raw_data_exists_and_has_reasonable_id_quality():

    df = _read_csv_from_gcs(BUCKET, RAW_DATA_BLOB)


    # assertions to check file exists, file is not empty and has an ID and BREAK columns
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "ID" in df.columns
    assert "BREAKS" in df.columns

    # IDs should not be missing
    assert df["ID"].notna().all(), "Found missing IDs in raw data"

    # Must have more than a handful of unique IDs
    n_rows = len(df)
    n_unique = df["ID"].nunique(dropna=True)
    assert n_unique > 10, f"Too few unique IDs: {n_unique}"
    assert n_unique / max(n_rows, 1) > 0.05, f"Unique ID ratio too low: {n_unique}/{n_rows}"


def test_prepared_data_schema_and_domain_rules():

    df = _read_csv_from_gcs(BUCKET, PREPARED_DATA_BLOB)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == EXPECTED_PREPARED_COLS
    assert df.isna().sum().sum() == 0

    # Check to test all numeric values are positive
    numeric_df = df.select_dtypes(include=["number"])
    
    # Find any negative values
    negatives = (numeric_df < 0)
    
    if negatives.any().any():
        negative_cols = numeric_df.columns[negatives.any()].tolist()
        raise AssertionError(
            f"Negative values found in numeric columns: {negative_cols}"
        )

    # One-hot integrity: allow 0 or 1 (0 means stage missing/unknown)
    for group in [
        ["smd_0", "smd_1", "smd_2", "smd_3", "smd_4"],
        ["aoi_0", "aoi_1", "aoi_2", "aoi_3", "aoi_4"],
        ["ss_0", "ss_1", "ss_2", "ss_3", "ss_4"],
        ["cc_0", "cc_1"],
    ]:
        s = df[group].sum(axis=1)
        assert ((s == 0) | (s == 1)).all(), f"Invalid one-hot rows for {group}: expected sum 0 or 1"


def test_model_exists_and_predictions_are_valid(tmp_path):

    # Load the model
    local_model = _download_model_from_gcs(BUCKET, MODEL_BLOB, str(tmp_path / "model.joblib"))
    model = joblib.load(local_model)

    # Load prepared data
    df = _read_csv_from_gcs(BUCKET, PREPARED_DATA_BLOB)

    # Use features the model was trained on
    if hasattr(model, "feature_names_in_"):
        feature_cols = list(model.feature_names_in_)
    else:
        raise AssertionError("Model does not have feature_names_in_. ")

    missing = [c for c in feature_cols if c not in df.columns]
    assert not missing, f"Prepared data missing model features: {missing}"

    # Make predictions on first 5 rows
    X = df[feature_cols]
    preds = model.predict(X.head(5))

    # Ensure predictions are valid number
    assert len(preds) == min(5, len(X))
    assert not np.isnan(preds).any()
    assert np.isfinite(preds).all()

    # Determinism
    sample = X.head(1)
    p1 = model.predict(sample)
    p2 = model.predict(sample)
    assert np.allclose(p1, p2)