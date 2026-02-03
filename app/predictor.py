import joblib
import pandas as pd

class Predictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

        # EXACT feature columns used during training
        self.feature_columns = [
            "job_id",
            "priority",

            "smd_0",
            "smd_1",
            "smd_2",
            "smd_3",
            "smd_4",
            "processing_time_s1",

            "aoi_0",
            "aoi_1",
            "aoi_2",
            "aoi_3",
            "aoi_4",
            "processing_time_s2",

            "ss_0",
            "ss_1",
            "ss_2",
            "ss_3",
            "ss_4",
            "processing_time_s3",

            "cc_0",
            "cc_1",
            "processing_time_s4",

            "overall_processing_time",
            "overall_waiting_time",
            "tardiness",
        ]

    def predict(self, instance: list) -> int:
        # Create 1-row DataFrame with correct column names
        df = pd.DataFrame([instance], columns=self.feature_columns)
        prediction = self.model.predict(df)[0]
        return int(prediction)
