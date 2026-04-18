import joblib
import pandas as pd

# Input feature expected by the model
FEATURE_COLUMNS = [
    "job_id",
    "priority",
    "family_type",
    "overall_processing_time",
    "overall_waiting_time",
    "tardiness",
]

class Predictor:
    # Load the trained model from the given file path
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    # Make a prediction using the loaded model
    def predict(self, features: dict) -> int:
        df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        pred = self.model.predict(df)[0]
        return int(pred)