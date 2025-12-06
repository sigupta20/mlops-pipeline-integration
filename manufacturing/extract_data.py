import os
import pandas as pd
from google.cloud import storage
import io


def extract_data():
    dfs = []

    client = storage.Client()
    BUCKET_NAME = 'ad-manufacturing-data-bucket'
    bucket = client.get_bucket(BUCKET_NAME)

    blobs = bucket.list_blobs()

    for blob in blobs:
        if(blob.name.endswith("_breakdowns.csv")):
            print(blob.name)
            content = blob.download_as_string()
            df = pd.read_csv(io.BytesIO(content))
            # print(df.to_string())
            if 'BREAKS' in df.columns:
                dfs.append(df)
    """
    # get data folder path
    folder_path = os.path.join(os.getcwd(), 'manufacturing', 'data')
    # Create list for DataFrames
    
    # Iterate through all subfolders in folder_path
    for subdir, dirs, files in os.walk(folder_path):
        for file in files:
                if 'breakdowns' in file:
                # Check if the file is a CSV file
                    if file.endswith('.csv'):
                        # Create a path to the current CSV file
                        file_path = os.path.join(subdir, file)
                        print(file_path)
                        # Read the CSV file and create a DataFrame
                        df = pd.read_csv(file_path)
                        if 'BREAKS' in df.columns:
                            dfs.append(df)
    """

    # Merge all DataFrames into a single DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)

    # Set pandas display options to show all columns
    pd.set_option('display.max_columns', None)

    print("\nDataFrame Head:")
    print(merged_df.head())
    print("-" * 20)

    # Return DataFrame as a list of lists
    return merged_df.values.tolist()


if __name__ == "__main__":
    extracted_data = extract_data()
    print(f"Data extraction complete.")
    print(f"Extracted {len(extracted_data)} records.")
