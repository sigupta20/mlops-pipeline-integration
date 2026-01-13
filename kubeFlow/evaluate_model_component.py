from typing import NamedTuple
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics

@component(
    base_image="python:3.10",
    packages_to_install=["pandas", "scikit-learn", "joblib"],
)
def evaluate_model_op(
    model: Input[Model],
    prepared_data: Input[Dataset],
    metrics: Output[Metrics],
    f1_threshold: float = 0.9,
) -> NamedTuple("Outputs", [("deploy_decision", str)]):
    import os
    import pandas as pd
    import joblib
    from sklearn.metrics import f1_score

    # Load data
    df = pd.read_csv(os.path.join(prepared_data.path, "prepared_data.csv"))
    X = df.drop("breaks", axis=1)
    y_true = df["breaks"]

    # Load model
    clf = joblib.load(os.path.join(model.path, "model.joblib"))

    # Predict
    y_pred = clf.predict(X)

    # Multiclass-safe F1
    f1 = f1_score(y_true, y_pred, average="weighted")
    metrics.log_metric("f1_score_weighted", f1)

    print(f"Weighted F1 score: {f1}")

    decision = "true" if f1 >= f1_threshold else "false"
    return (decision,)
