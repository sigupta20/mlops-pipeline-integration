import joblib
import pandas as pd

class Predictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def predict(self, features: dict) -> int:
        df = pd.DataFrame([features])
        prediction = self.model.predict(df)[0]
        return int(prediction)
