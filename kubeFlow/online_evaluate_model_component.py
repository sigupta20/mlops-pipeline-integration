from kfp.dsl import component, Dataset, Output, Input, Model, Metrics, Artifact

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310:latest",
    packages_to_install=[
        "pandas",
        "scikit-learn",
        "google-cloud-aiplatform",
        "google-cloud-bigquery",
    ],
)
def online_evaluate_model_op(
    project_id: str,
    location: str,
    bq_table: str,
    retrain_decision: Output[str],
    f1_threshold: float = 0.9,
    max_samples: int = 100,
):
    from google.cloud import aiplatform
    from google.cloud import bigquery
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score

    # -------------------------------
    # 1. Init Vertex AI
    # -------------------------------
    aiplatform.init(
        project=project_id,
        location=location,
    )

    endpoints = aiplatform.Endpoint.list()

    if not endpoints:
        print("No endpoint found. Retraining required.")
        with open(retrain_decision.path, "w") as f:
            f.write("true")
        return

    endpoint = endpoints[0]

    # -------------------------------
    # 2. Load evaluation data
    # -------------------------------
    bq_client = bigquery.Client(project=project_id)

    query = f"""
        SELECT
            overall_processing_time,
            tardiness,
            breaks
        FROM `{bq_table}`
    """

    df = bq_client.query(query).result().to_dataframe()

    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=52,
    )

    X_test = X_test.tail(max_samples)
    y_test = y_test.tail(max_samples)

    # -------------------------------
    # 3. Online prediction
    # -------------------------------
    predictions = endpoint.predict(
        instances=X_test.to_numpy().tolist()
    )

    y_pred_binary = [int(p) for p in predictions.predictions]
    y_true_binary = (y_test != 0).astype(int)

    # -------------------------------
    # 4. Evaluate
    # -------------------------------
    f1 = f1_score(
        y_true_binary,
        y_pred_binary,
        average="weighted",
    )

    print("Online F1 score:", f1)

    # -------------------------------
    # 5. Retrain decision
    # -------------------------------
    retrain = f1 < f1_threshold

    with open(retrain_decision.path, "w") as f:
        f.write(str(retrain).lower())

    if retrain:
        print("Performance degraded. Retraining required.")
    else:
        print("Model performance acceptable.")
