import pandas as pd
import joblib
import db_dtypes
from google.cloud import bigquery
from google.cloud import aiplatform
from google.cloud import storage
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score


def knn(): 
    client = bigquery.Client(
        project='mlops-pipeline-01',
        location='europe-west1'
    )
    # SQL query to load the data
    print("SQL query to load the data")
    sql_query = """
        SELECT priority, smd_0, smd_1, smd_2, smd_3, smd_4, 
            processing_time_s1, aoi_0, aoi_1, aoi_2, aoi_3, aoi_4,
            processing_time_s2, ss_0, ss_1, ss_2, ss_3, ss_4, 
            processing_time_s3, cc_0, cc_1, processing_time_s4, 
            overall_processing_time, overall_waiting_time, tardiness, breaks  
        FROM mlops-pipeline-01.manufacturing_data.manufacturing;
    """

    # Loading data into a Panda DataFrame
    print("Loading data into a Panda DataFrame")
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

    # Define the target variable (in this case it is 'breaks')
    target = 'breaks'

    # Separate features and target variables
    X = df.drop(target, axis=1)
    y = df[target]

    # Split into training and test sets
    print("Split into training and test sets")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    # Create the KNN model
    print("Create the KNN model")
    knn_model = KNeighborsClassifier(n_neighbors=5, metric='minkowski')

    # Train the model
    print("Train the model")
    knn_model.fit(X_train, y_train)

    # Make predictions on the test data-set
    print("Make predictions on the test data-set")
    y_pred = knn_model.predict(X_test)

    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int) 

    # Evaluation of the model (e.g., accuracy)
    print("Evaluation of the model (e.g., accuracy)")
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test_binary, y_pred_binary, average='binary')

    print(f'Accuracy for "breaks": {accuracy}')
    print(f'F1-Score for "breaks": {f1}')


    # Saving the model with joblib
    print("Saving the model with joblib")
    artifact_filename = 'model.joblib'

    joblib.dump(knn_model, artifact_filename)

    storage_client = storage.Client()
    bucket_name = 'ad-manufacturing-data-bucket'
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(artifact_filename)
    blob.upload_from_filename(artifact_filename)

    # Retrieve URL of uploaded model
    #artifact_uri = f"gs://{bucket_name}/{artifact_filename}"
    artifact_uri = f"gs://{bucket_name}/"


    print(artifact_uri)
    # Configuring the serving container image
    print("Configuring the serving container image")
    container_image_uri = "europe-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest"
    print("AI Platform")
    # Creating the model object
    print("Creating the model object")
    aiplatform.init(project="mlops-pipeline-01", location="europe-west1")
    model = aiplatform.Model.upload(
        display_name='knn_model',
        artifact_uri=artifact_uri,
        serving_container_image_uri=container_image_uri
    )

    #Printing the provided model resource
    print("Model deployed:", model.resource_name)

if __name__ == "__main__":
    knn()
