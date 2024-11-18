import pandas as pd
import joblib
from google.cloud import bigquery
from google.cloud import aiplatform
from google.cloud import storage
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.metrics import f1_score
from airflow.exceptions import AirflowFailException

def bagging_knn(): 
    client = bigquery.Client()
    # SQL Query
    sql_query = """
        SELECT job_id, overall_processing_time, tardiness, breaks  
        FROM airflow-408713.manufacturing_data.manufacturing;
    """

    data = client.query(sql_query).result().to_dataframe()
    column_names = [
        "job_id",
        "overall_processing_time", 
        "tardiness", 
        "breaks"
    ]
    # Load data into pandas data frame
    df = pd.DataFrame(data, columns=column_names)

    # Define target attribute
    target = 'breaks'

    # Seperate features and target attribute
    X = df.drop(target, axis=1)
    y = df[target]

    # Split data into test and training data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Create KNN Model
    knn_model = KNeighborsClassifier(n_neighbors=5, metric='minkowski')
    knn_model.fit(X_train, y_train)

    # Create Model based on knn
    bagging_model = BaggingClassifier(estimator=knn_model, n_estimators=10, random_state=42)

    # Train model
    bagging_model.fit(X_train, y_train)

    # Predict test data
    y_pred = bagging_model.predict(X_test)

    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    # Evaluate model performance
    f1 = f1_score(y_test_binary, y_pred_binary, average='binary')
    print(f'F1-Score des Bagging-Modells für "breaks": {f1}')

    # Evaluate Model performance
    if(f1 < 0.9):    
        raise AirflowFailException("model performance is too low")

    # Speichern des Modells mit joblib
    artifact_filename = 'model.joblib'

    joblib.dump(knn_model, artifact_filename)

    storage_client = storage.Client()
    bucket_name = 'csv-manufacturing-data-bucket'
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(artifact_filename)
    blob.upload_from_filename(artifact_filename)
    
    print("Successfully uploaded model to cloud")
    
    