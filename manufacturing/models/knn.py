import pandas as pd
import joblib
from google.cloud import bigquery
from google.cloud import aiplatform
from google.cloud import storage
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score

def knn(): 
    client = bigquery.Client()
    # SQL-Abfrage zum Laden der Daten
    sql_query = """
        SELECT priority, smd_0, smd_1, smd_2, smd_3, smd_4, 
            processing_time_s1, aoi_0, aoi_1, aoi_2, aoi_3, aoi_4,
            processing_time_s2, ss_0, ss_1, ss_2, ss_3, ss_4, 
            processing_time_s3, cc_0, cc_1, processing_time_s4, 
            overall_processing_time, overall_waiting_time, tardiness, breaks  
        FROM airflow-408713.manufacturing_data.manufacturing;
    """

    # Daten in ein Pandas DataFrame laden
    data = client.query(sql_query).result().to_dataframe()
    
    column_names = ["smd_0", "smd_1", "smd_2", 
                    "smd_3", "smd_4", "aoi_0", 
                    "aoi_1", "aoi_2", "aoi_3",
                    "aoi_4", "ss_0", "ss_1", 
                    "ss_2", "ss_3", "ss_4",
                    "cc_0", "cc_1", 
                    "overall_processing_time", 
                    "tardiness", "breaks"]
    df = pd.DataFrame(data, columns=column_names)

    # Zielvariable (target) definieren (in diesem Fall ist es 'breaks')
    target = 'breaks'

    # Features und Zielvariable trennen
    X = df.drop(target, axis=1)
    y = df[target]

    # Aufteilung in Trainings- und Testsets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Erstelle das KNN-Modell
    knn_model = KNeighborsClassifier(n_neighbors=5, metric='minkowski')

    # Trainiere das Modell
    knn_model.fit(X_train, y_train)

    # Mache Vorhersagen auf dem Testset
    y_pred = knn_model.predict(X_test)

    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int) 

    # Evaluierung des Modells (z.B. Genauigkeit)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average='binary')

    print(f'Accuracy for "breaks": {accuracy}')
    print(f'F1-Score for "breaks": {f1}')


    # Speichern des Modells mit joblib
    artifact_filename = 'model.joblib'

    joblib.dump(knn_model, artifact_filename)

    storage_client = storage.Client()
    bucket_name = 'csv-manufacturing-data-bucket'
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(artifact_filename)
    blob.upload_from_filename(artifact_filename)

    # URL des hochgeladenen Modells abrufen
    #artifact_uri = f"gs://{bucket_name}/{artifact_filename}"
    artifact_uri = f"gs://{bucket_name}/"


    print(artifact_uri)
    # Konfigurieren des Serving-Container-Images
    container_image_uri = "europe-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest"
    print("AI Platform")
    # Erstellen des Modellobjekts
    aiplatform.init(project="airflow-408713", location="europe-west1")
    model = aiplatform.Model.upload(
        display_name='knn_model',
        artifact_uri=artifact_uri,
        serving_container_image_uri=container_image_uri
    )

    # Drucken der bereitgestellten Modellressource
    print("Model deployed:", model.resource_name)


