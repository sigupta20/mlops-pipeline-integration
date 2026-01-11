from typing import NamedTuple
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310:latest",
    packages_to_install=["pandas", "scikit-learn", "joblib"],
)
def evaluate_model_op(
    model: Input[Model],
    prepared_data: Input[Dataset],
    metrics: Output[Metrics],
    f1_threshold: float = 0.9,
) -> NamedTuple("Outputs", [("deploy_decision", str)]):
    import pandas as pd
    import joblib
    import json
    import os

    from sklearn.metrics import f1_score, accuracy_score
    from sklearn.model_selection import train_test_split

    # -------------------------------
    # 1. Load model
    # -------------------------------
    model_path = os.path.join(model.path, "model.joblib")
    knn = joblib.load(model_path)

    # -------------------------------
    # 2. Load prepared data
    # -------------------------------
    data_path = os.path.join(prepared_data.path, "prepared_data.csv")
    df = pd.read_csv(data_path)

    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    # -------------------------------
    # 3. Evaluation split
    # -------------------------------
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.3, random_state=52
    )

    # -------------------------------
    # 4. Predict & evaluate
    # -------------------------------
    y_pred = knn.predict(X_test)

    y_test_binary = (y_test != 0).astype(int)
    y_pred_binary = (y_pred != 0).astype(int)

    f1 = f1_score(y_test_binary, y_pred_binary)
    accuracy = accuracy_score(y_test, y_pred)

    metrics_dict = {
        "f1_score": f1,
        "accuracy": accuracy,
    }

    # -------------------------------
    # 5. Save metrics artifact
    # -------------------------------
    deploy = f1 >= f1_threshold

    metrics.log_metric("f1_score", f1)
    metrics.log_metric("accuracy", accuracy)
    return ("true" if deploy else "false",)
