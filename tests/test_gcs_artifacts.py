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
    "smd_0",
    "smd_1",
    "smd_2",
    "smd_3",
    "smd_4",
    "processing_time_s1",
    "aoi_0",
    "aoi_1",
    "aoi_2",
    "aoi_3",
    "aoi_4",
    "processing_time_s2",
    "ss_0",
    "ss_1",
    "ss_2",
    "ss_3",
    "ss_4",
    "processing_time_s3",
    "cc_0",
    "cc_1",
    "processing_time_s4",
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


def test_raw_data_exists_and_has_no_duplicate_ids():
    df = _read_csv_from_gcs(BUCKET, RAW_DATA_BLOB)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "ID" in df.columns

    dup = df.duplicated(subset=["ID"], keep=False).sum()
    assert dup == 0, f"Found {dup} duplicate IDs"


def test_prepared_data_schema_and_domain_rules():
    df = _read_csv_from_gcs(BUCKET, PREPARED_DATA_BLOB)

    assert not df.empty
    assert list(df.columns) == EXPECTED_PREPARED_COLS
    assert df.isna().sum().sum() == 0

    for c in [
        "processing_time_s1",
        "processing_time_s2",
        "processing_time_s3",
        "processing_time_s4",
        "overall_processing_time",
        "overall_waiting_time",
    ]:
        assert (df[c] >= 0).all(), f"Negative values found in {c}"

    assert (df[["smd_0","smd_1","smd_2","smd_3","smd_4"]].sum(axis=1) == 1).all()
    assert (df[["aoi_0","aoi_1","aoi_2","aoi_3","aoi_4"]].sum(axis=1) == 1).all()
    assert (df[["ss_0","ss_1","ss_2","ss_3","ss_4"]].sum(axis=1) == 1).all()
    assert (df[["cc_0","cc_1"]].sum(axis=1) == 1).all()


def test_model_exists_and_predictions_are_valid(tmp_path):
    local_model = _download_model_from_gcs(
        BUCKET, MODEL_BLOB, str(tmp_path / "model.joblib")
    )
    model = joblib.load(local_model)

    df = _read_csv_from_gcs(BUCKET, PREPARED_DATA_BLOB)
    X = df.drop("breaks", axis=1)

    preds = model.predict(X.head(5))
    assert len(preds) == min(5, len(X))
    assert not np.isnan(preds).any()
    assert np.isfinite(preds).all()

    sample = X.head(1)
    p1 = model.predict(sample)
    p2 = model.predict(sample)
    assert np.allclose(p1, p2)