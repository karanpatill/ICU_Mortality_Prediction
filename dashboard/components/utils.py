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

_REAL_DATA = BASE_DIR / "data" / "mimiciv" / "mimiciv_ventilated_cohort_24h.csv"
_DEMO_DATA = BASE_DIR / "data" / "demo" / "demo_cohort.csv"
_MIMIC_10_PATH = BASE_DIR / "data" / "mimic_10_patients.json"

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
FRESH_MAX = 6.0       # < 6h  -> Fresh
MODERATE_MAX = 20.0   # 6-20h -> Moderate
# 20-48h -> Stale
# >= 48h -> Sentinel

# Risk thresholds
RISK_STABLE   = 25    # < 25%  -> STABLE
RISK_WATCH    = 50    # 25-50% -> WATCH
RISK_ELEVATED = 70    # 50-70% -> ELEVATED
# > 70%  -> CRITICAL

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_raw_data():
    """Load full cohort dataset."""
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

@st.cache_data(show_spinner=False)
def load_mimic_10_cohort():
    """Load the verified 10 Real MIMIC-IV Clinical Patients."""
    with open(_MIMIC_10_PATH, "r") as f:
        return json.load(f)

# ─── Feature Engineering ──────────────────────────────────────────────────────
def encode_features(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    df = df.copy()
    if "gender" in df.columns:
        df["gender"] = (df["gender"] == "M").astype(int)
    df = pd.get_dummies(df, columns=["first_careunit", "admission_type"], drop_first=False)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    return df[feature_cols].astype(float)

def predict_risk(patient_df: pd.DataFrame, model, schema: dict) -> np.ndarray:
    feature_cols = schema["features"]
    X = encode_features(patient_df, feature_cols)
    probs = model.predict_proba(X)[:, 1]
    return probs

# ─── Staleness & Risk Classifiers ─────────────────────────────────────────────
def classify_staleness(hours: float) -> dict:
    if hours >= SENTINEL_HOURS:
        return {"label": "Sentinel", "color": "#6e7681", "bg": "#1c2128", "text_color": "#8b949e"}
    elif hours >= MODERATE_MAX:
        return {"label": "Stale", "color": "#ff1744", "bg": "#2b0a0d", "text_color": "#ff8097"}
    elif hours >= FRESH_MAX:
        return {"label": "Moderate", "color": "#ffb700", "bg": "#2b1c00", "text_color": "#ffe082"}
    else:
        return {"label": "Fresh", "color": "#00e676", "bg": "#0d2b12", "text_color": "#69f0ae"}

def classify_risk(risk_pct: float) -> dict:
    if risk_pct >= RISK_ELEVATED:
        return {"label": "CRITICAL", "color": "#ff1744"}
    elif risk_pct >= RISK_WATCH:
        return {"label": "ELEVATED", "color": "#ff9100"}
    elif risk_pct >= RISK_STABLE:
        return {"label": "WATCH", "color": "#ffd600"}
    else:
        return {"label": "STABLE", "color": "#00e676"}

# ─── 10 Real MIMIC-IV Ward Dataset ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_ward_patients(n_beds: int = 10):
    """
    Returns the 10 Real MIMIC-IV Patients with pre-computed LightGBM risk scores.
    """
    pts = load_mimic_10_cohort()
    df_pts = pd.DataFrame(pts)
    model = load_model()
    schema = load_schema()
    
    X = encode_features(df_pts, schema["features"])
    probs = model.predict_proba(X)[:, 1]
    
    df_pts["risk_score"] = probs
    df_pts["risk_pct"] = (probs * 100.0).round(1)
    df_pts["bed_id"] = [f"BED-{i+1:02d}" for i in range(len(df_pts))]
    return df_pts

# ─── Feature Importance ───────────────────────────────────────────────────────
def get_feature_importance(model, schema: dict, top_n: int = 15) -> pd.DataFrame:
    feature_names = schema["features"]
    importances = model.feature_importances_
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
    patient_df = pd.DataFrame([base_patient.to_dict()])
    for col, val in overrides.items():
        patient_df[col] = val
    probs = predict_risk(patient_df, model, schema)
    return float(probs[0])
