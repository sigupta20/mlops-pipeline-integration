import os
import pandas as pd
from google.cloud import storage
import io


def extract_data():
    dfs = []

    client = storage.Client()
    BUCKET_NAME = 'csv-manufacturing-data-bucket'
    bucket = client.get_bucket(BUCKET_NAME)

    blobs = bucket.list_blobs()

    for blob in blobs:
        if(blob.name.endswith("_breakdowns.csv")):
            print(blob.name)
            content = blob.download_as_string()
            df = pd.read_csv(io.BytesIO(content))
            if 'BREAKS' in df.columns:
                dfs.append(df)

    # get data folder path
    folder_path = os.path.join(os.getcwd(), 'dags', 'manufacturing', 'data')
    # Liste für DataFrames erstellen
    
    """
    # Durchlaufe alle Unterordner in folder_path
    for subdir, dirs, files in os.walk(folder_path):
        for file in files:
                if 'breakdowns' in file:
                # Überprüfen, ob die Datei eine CSV-Datei ist
                    if file.endswith('.csv'):
                        # Pfad zur aktuellen CSV-Datei erstellen
                        file_path = os.path.join(subdir, file)
                        print(file_path)
                        # CSV-Datei lesen und DataFrame erstellen
                        df = pd.read_csv(file_path)
                        if 'BREAKS' in df.columns:
                            dfs.append(df)
    """

    # Alle DataFrames zu einem einzigen DataFrame zusammenführen
    merged_df = pd.concat(dfs, ignore_index=True)

    # DataFrame als Liste von Listen zurückgeben
    return merged_df.values.tolist()
