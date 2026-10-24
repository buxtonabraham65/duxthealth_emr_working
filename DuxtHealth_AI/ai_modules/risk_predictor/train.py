# Placeholder for ai_modules/risk_predictor/train.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from model import RiskPredictor
from utils import prepare_features


def train_model(data_path: str):
    print("Loading dataset...")
    df = pd.read_csv(data_path)

    if "risk_outcome" not in df.columns:
        raise ValueError("Dataset must contain 'risk_outcome' column")

    X = df.drop(columns=["risk_outcome"])
    y = df["risk_outcome"]

    X = prepare_features(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RiskPredictor()
    model.train(X_train, y_train)

    # Evaluation
    preds = model.predict_class(X_test)
    probs = model.predict_probability(X_test)

    print("\nModel Evaluation:")
    print("Accuracy:", accuracy_score(y_test, preds))
    print("ROC AUC:", roc_auc_score(y_test, probs))
    print(classification_report(y_test, preds))

    print("Model saved successfully.")


if __name__ == "__main__":
    train_model("mock_patient_data.csv")
