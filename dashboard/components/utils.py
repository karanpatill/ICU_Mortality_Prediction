# utils.py - Core data loading, model inference, and feature engineering
# AURA-ICU: Dynamic Clinical Decision Support System
# D. Y. Patil School of Engineering and Management, Kolhapur

import pandas as pd
import numpy as np
import joblib
import json
import streamlit as st
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # D:\ICU_Mortality_Prediction

# Auto-detect: use real MIMIC-IV data locally, synthetic demo data on deployment
_REAL_DATA = BASE_DIR / "data" / "mimiciv" / "mimiciv_ventilated_cohort_24h.csv"
_DEMO_DATA = BASE_DIR / "data" / "demo" / "demo_cohort.csv"
DATA_PATH = _REAL_DATA if _REAL_DATA.exists() else _DEMO_DATA
IS_DEMO_MODE = not _REAL_DATA.exists()

MODEL_PATH = BASE_DIR / "models" / "lightgbm_staleness_production.joblib"
SCHEMA_PATH = BASE_DIR / "models" / "feature_schema.json"

# ─── Constants ────────────────────────────────────────────────────────────────
SENTINEL_HOURS = 48.0
LAB_NAMES = [
    "creatinine", "bun", "potassium", "sodium", "glucose",
    "platelets", "wbc", "hemoglobin", "lactate", "pao2",
    "paco2", "ph", "bilirubin"
]
LAB_DISPLAY = {
    "creatinine": "Creatinine", "bun": "BUN", "potassium": "Potassium",
    "sodium": "Sodium", "glucose": "Glucose", "platelets": "Platelets",
    "wbc": "WBC", "hemoglobin": "Hemoglobin", "lactate": "Lactate",
    "pao2": "PaO2", "paco2": "PaCO2", "ph": "pH", "bilirubin": "Bilirubin"
}
LAB_UNITS = {
    "creatinine": "mg/dL", "bun": "mg/dL", "potassium": "mEq/L",
    "sodium": "mEq/L", "glucose": "mg/dL", "platelets": "K/uL",
    "wbc": "K/uL", "hemoglobin": "g/dL", "lactate": "mmol/L",
    "pao2": "mmHg", "paco2": "mmHg", "ph": "", "bilirubin": "mg/dL"
}
LAB_NORMAL = {
    "creatinine": (0.6, 1.2), "bun": (7, 20), "potassium": (3.5, 5.0),
    "sodium": (136, 145), "glucose": (70, 100), "platelets": (150, 400),
    "wbc": (4.0, 11.0), "hemoglobin": (12.0, 17.5), "lactate": (0.5, 2.0),
    "pao2": (75, 100), "paco2": (35, 45), "ph": (7.35, 7.45),
    "bilirubin": (0.1, 1.2)
}

# Staleness thresholds
FRESH_MAX = 6.0       # < 6h  -> Fresh (green)
MODERATE_MAX = 20.0   # 6-20h -> Moderate (yellow)
# 20-48h -> Stale (red)
# >= 48h -> Sentinel (gray)

# Risk thresholds
RISK_STABLE   = 25    # < 25%  -> STABLE (green)
RISK_WATCH    = 50    # 25-50% -> WATCH (yellow)
RISK_ELEVATED = 70    # 50-70% -> ELEVATED (orange)
# > 70%  -> CRITICAL (red)

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_raw_data():
    """Load full MIMIC-IV cohort CSV."""
    df = pd.read_csv(DATA_PATH)
    return df

@st.cache_resource(show_spinner=False)
def load_model():
    """Load trained LightGBM model."""
    return joblib.load(MODEL_PATH)

@st.cache_data(show_spinner=False)
def load_schema():
    """Load feature schema."""
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

# ─── Feature Engineering (must match training pipeline EXACTLY) ───────────────
def encode_features(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Encode a DataFrame exactly as done during training:
    1. gender M=1, F=0
    2. get_dummies for first_careunit and admission_type
    3. Reindex to training feature set, fill missing with 0
    """
    df = df.copy()
    df["gender"] = (df["gender"] == "M").astype(int)
    df = pd.get_dummies(df, columns=["first_careunit", "admission_type"], drop_first=False)
    # Align to training feature set
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    return df[feature_cols].astype(float)

def predict_risk(patient_df: pd.DataFrame, model, schema: dict) -> np.ndarray:
    """
    Given a raw patient DataFrame (with original columns), return mortality
    risk probabilities as numpy array (values between 0 and 1).
    """
    feature_cols = schema["features"]
    X = encode_features(patient_df, feature_cols)
    probs = model.predict_proba(X)[:, 1]
    return probs

# ─── Staleness Classification ─────────────────────────────────────────────────
def classify_staleness(hours: float) -> dict:
    """
    Returns color, label, and emoji for a given staleness value in hours.
    """
    if hours >= SENTINEL_HOURS:
        return {"label": "Sentinel", "color": "#6c757d", "bg": "#2d2d2d",
                "emoji": "S", "text_color": "#adb5bd"}
    elif hours >= MODERATE_MAX:
        return {"label": "Stale", "color": "#dc3545", "bg": "#2d0a0d",
                "emoji": "!", "text_color": "#ff6b7a"}
    elif hours >= FRESH_MAX:
        return {"label": "Moderate", "color": "#ffc107", "bg": "#2d2200",
                "emoji": "~", "text_color": "#ffd966"}
    else:
        return {"label": "Fresh", "color": "#28a745", "bg": "#0a2d0f",
                "emoji": "OK", "text_color": "#5cb85c"}

def classify_risk(risk_pct: float) -> dict:
    """Returns color and label for a given risk percentage (0-100)."""
    if risk_pct >= RISK_ELEVATED:
        return {"label": "CRITICAL", "color": "#dc3545", "badge_color": "#dc3545"}
    elif risk_pct >= RISK_WATCH:
        return {"label": "ELEVATED", "color": "#fd7e14", "badge_color": "#fd7e14"}
    elif risk_pct >= RISK_STABLE:
        return {"label": "WATCH", "color": "#ffc107", "badge_color": "#ffc107"}
    else:
        return {"label": "STABLE", "color": "#28a745", "badge_color": "#28a745"}

# ─── Ward Patient Sampling ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_ward_patients(n_beds: int = 12):
    """
    Sample n_beds patients from the dataset with diverse risk/unit spread.
    Returns raw DataFrame (no encoding) PLUS computed risk scores.
    """
    df_raw = load_raw_data()
    model = load_model()
    schema = load_schema()
    feature_cols = schema["features"]

    # Compute risk for all patients
    X_all = encode_features(df_raw, feature_cols)
    all_risks = model.predict_proba(X_all)[:, 1]
    df_raw = df_raw.copy()
    df_raw["risk_score"] = all_risks

    # Sample diversely: 3 critical, 3 elevated, 3 watch, 3 stable
    buckets = []
    for lo, hi, n in [(0.70, 1.00, 3), (0.50, 0.70, 3), (0.25, 0.50, 3), (0.00, 0.25, 3)]:
        bucket = df_raw[(df_raw["risk_score"] >= lo) & (df_raw["risk_score"] < hi)]
        if len(bucket) >= n:
            buckets.append(bucket.sample(n=n, random_state=42))
        elif len(bucket) > 0:
            buckets.append(bucket.sample(n=min(n, len(bucket)), random_state=42))

    ward_df = pd.concat(buckets, ignore_index=True).head(n_beds)
    ward_df["bed_id"] = [f"BED-{i+1:02d}" for i in range(len(ward_df))]
    ward_df["risk_pct"] = (ward_df["risk_score"] * 100).round(1)
    return ward_df

# ─── Feature Importance ───────────────────────────────────────────────────────
def get_feature_importance(model, schema: dict, top_n: int = 15) -> pd.DataFrame:
    """
    Get LightGBM split-based feature importance (top N).
    Marks staleness features distinctly.
    """
    feature_names = schema["features"]
    importances = model.feature_importances_  # built-in LightGBM split importance
    df_imp = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False).head(top_n)
    df_imp["is_staleness"] = df_imp["feature"].str.endswith("_staleness")
    df_imp["display_name"] = df_imp["feature"].str.replace("first_careunit_", "Unit: ", regex=False)\
                                               .str.replace("admission_type_", "Admit: ", regex=False)\
                                               .str.replace("_val", " (Value)", regex=False)\
                                               .str.replace("_staleness", " (Staleness)", regex=False)
    return df_imp.reset_index(drop=True)

# ─── Patient Staleness Summary ────────────────────────────────────────────────
def get_staleness_summary(patient_row: pd.Series) -> dict:
    """
    Returns dict of lab -> staleness classification for a single patient.
    """
    result = {}
    for lab in LAB_NAMES:
        col = f"{lab}_staleness"
        hours = float(patient_row.get(col, SENTINEL_HOURS))
        result[lab] = {
            "hours": hours,
            "classification": classify_staleness(hours),
            "value": float(patient_row.get(f"{lab}_val", np.nan)),
            "display": LAB_DISPLAY[lab],
            "unit": LAB_UNITS[lab],
            "normal": LAB_NORMAL[lab]
        }
    return result

# ─── What-If Prediction ───────────────────────────────────────────────────────
def whatif_predict(base_patient: pd.Series, overrides: dict, model, schema: dict) -> float:
    """
    Given a base patient row and a dict of {col: new_value} overrides,
    return new risk probability (0-1).
    """
    patient_df = pd.DataFrame([base_patient.to_dict()])
    for col, val in overrides.items():
        patient_df[col] = val
    probs = predict_risk(patient_df, model, schema)
    return float(probs[0])
