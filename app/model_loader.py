from google.cloud import storage

def load_model_from_gcs(bucket_name, blob_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    local_path = "/tmp/model.joblib"
    blob.download_to_filename(local_path)
    return local_path
