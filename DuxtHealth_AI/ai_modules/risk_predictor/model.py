# Placeholder for ai_modules/risk_predictor/model.py
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.pkl")


class RiskPredictor:
    def __init__(self):
        self.pipeline = None

        if os.path.exists(MODEL_PATH):
            self.load_model()
        else:
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("model", RandomForestClassifier(
                    n_estimators=300,
                    max_depth=10,
                    class_weight="balanced",
                    random_state=42
                ))
            ])

    def train(self, X: pd.DataFrame, y: pd.Series):
        self.pipeline.fit(X, y)
        self.save_model()

    def predict_probability(self, X: pd.DataFrame):
        """
        Returns probability of high risk (0–1)
        """
        probs = self.pipeline.predict_proba(X)
        return probs[:, 1]

    def predict_class(self, X: pd.DataFrame):
        return self.pipeline.predict(X)

    def save_model(self):
        joblib.dump(self.pipeline, MODEL_PATH)

    def load_model(self):
        self.pipeline = joblib.load(MODEL_PATH)
