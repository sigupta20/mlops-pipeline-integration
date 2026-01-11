from kfp.dsl import component, Dataset, Output

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310:latest",
    packages_to_install=[
        "pandas",
        "google-cloud-storage<3",
    ],
)
def extract_data_op(
    bucket_name: str,
    raw_data: Output[Dataset],
):
    import pandas as pd
    from google.cloud import storage
    import io
    import os

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    dfs = []

    for blob in bucket.list_blobs():
        if blob.name.endswith("_breakdowns.csv"):
            print(blob.name)
            content = blob.download_as_string()
            df = pd.read_csv(io.BytesIO(content))

            if "BREAKS" in df.columns:
                dfs.append(df)

    if not dfs:
        raise RuntimeError("No valid CSV files found in bucket")

    # Merge all DataFrames into a single DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)

    os.makedirs(raw_data.path, exist_ok=True)
    output_path = os.path.join(raw_data.path, "raw_data.csv")
    merged_df.to_csv(output_path, index=False)

    print(f"Raw data written to {output_path}")
