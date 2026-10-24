# Placeholder for ai_modules/risk_predictor/utils.py
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = [
    "age",
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    "respiratory_rate",
    "temperature",
    "oxygen_saturation",
    "previous_hospitalizations",
    "chronic_conditions_count"
]


def validate_input(df: pd.DataFrame):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Pulse pressure
    df["pulse_pressure"] = df["systolic_bp"] - df["diastolic_bp"]

    # Early warning style composite
    df["ews_score"] = (
        (df["heart_rate"] > 100).astype(int) +
        (df["oxygen_saturation"] < 92).astype(int) +
        (df["temperature"] > 38).astype(int)
    )

    return df


def prepare_features(df: pd.DataFrame):
    validate_input(df)
    df = feature_engineering(df)
    return df

