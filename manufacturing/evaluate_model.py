from google.cloud import aiplatform
import pandas as pd
import numpy as np

from google.cloud import bigquery
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

def evaluate_model(
    project: str,
    location: str,
    ):  

    # Init VertexAI
    aiplatform.init(project=project, location=location)

    endpoints = aiplatform.Endpoint.list()
    if len(endpoints) == 0:
       print("No endpoints exist")
       return True
    
    # Get Data and split into test and training set

    client = bigquery.Client()
    # SQL Query
    sql_query = """
        SELECT job_id, overall_processing_time, tardiness, breaks  
        FROM airflow-408713.manufacturing_data.manufacturing;
    """

    data = client.query(sql_query).result().to_dataframe()
    
    # Split data into features (X) and target (y)
    X = data.drop('breaks', axis=1)
    y = data['breaks']
    
    # Split data into test and training data
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.3, random_state=52)

    X_test_np = X_test[-100:].to_numpy()
    y_test = y_test[-100:]

    endpoints = aiplatform.Endpoint.list()
    if len(endpoints) == 0:
        print("No endpoints exist")
        return True

    # Predict from VertexAI
    x_predict = endpoints[0].predict(instances=X_test_np.tolist())

    x_predict_binary = [int(prediction) for prediction in x_predict.predictions]
    y_test_binary = (y_test != 0).astype(int)

    # Evaluate model performance
    f1 = f1_score(y_test_binary, x_predict_binary, average='weighted')
    print(f'F1-Score des Bagging-Modells für "breaks": {f1}')

    # Evaluate Model performance
    if(f1 > 0.9):    
       return False
    
    print("F1 is too small. Trigger new dag run")
    return True
    
    