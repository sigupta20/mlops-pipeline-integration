from kfp.dsl import component, Dataset, Output, Input, Model

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310:latest",
    packages_to_install=[
        "pandas",
        "scikit-learn",
        "joblib",
    ],
)
def train_knn_op(
    prepared_data: Input[Dataset],
    model: Output[Model],
    n_neighbors: int = 5,
):
    import pandas as pd
    import joblib
    import os

    from sklearn.neighbors import KNeighborsClassifier

    # -------------------------------
    # 1. Load prepared dataset
    # -------------------------------
    data_path = os.path.join(prepared_data.path, "prepared_data.csv")
    df = pd.read_csv(data_path)

    # -------------------------------
    # 2. Split features / target
    # -------------------------------
    X = df.drop("breaks", axis=1)
    y = df["breaks"]

    # -------------------------------
    # 3. Train KNN model (FULL DATA)
    # -------------------------------
    knn = KNeighborsClassifier(
        n_neighbors=n_neighbors,
        metric="minkowski",
    )
    knn.fit(X, y)

    # -------------------------------
    # 4. Save model artifact
    # -------------------------------
    os.makedirs(model.path, exist_ok=True)
    model_path = os.path.join(model.path, "model.joblib")
    joblib.dump(knn, model_path)

    print("Model training completed")
    print(f"Model saved to: {model_path}")
