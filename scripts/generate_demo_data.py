# generate_demo_data.py
# Generates synthetic ICU patient data for public demo (GitHub/Streamlit Cloud)
# Real MIMIC-IV data is NOT included in repo (PhysioNet DUA restrictions)
# D. Y. Patil School of Engineering and Management, Kolhapur

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
N = 2000  # synthetic patients for demo

CARE_UNITS = [
    "Medical Intensive Care Unit (MICU)",
    "Surgical Intensive Care Unit (SICU)",
    "Coronary Care Unit (CCU)",
    "Medical/Surgical Intensive Care Unit (MICU/SICU)",
    "Trauma SICU (TSICU)",
    "Neuro Surgical Intensive Care Unit (Neuro SICU)",
    "Intensive Care Unit (ICU)",
]
ADMIT_TYPES = [
    "EMERGENCY", "DIRECT EMER.", "ELECTIVE", "URGENT",
    "EW EMER.", "SURGICAL SAME DAY ADMISSION"
]

def synthetic_lab(mean, std, n, low=None, high=None):
    vals = np.random.normal(mean, std, n)
    if low is not None:
        vals = np.clip(vals, low, None)
    if high is not None:
        vals = np.clip(vals, None, high)
    return vals.round(2)

def synthetic_staleness(n, sentinel_prob=0.15, stale_prob=0.20, moderate_prob=0.30):
    """Sample staleness values with realistic ICU distribution."""
    cats = np.random.choice(
        ["sentinel", "stale", "moderate", "fresh"],
        p=[sentinel_prob, stale_prob, moderate_prob, 1-sentinel_prob-stale_prob-moderate_prob],
        size=n
    )
    result = np.zeros(n)
    result[cats == "sentinel"] = 48.0
    result[cats == "stale"]    = np.random.uniform(20, 47.9, (cats == "stale").sum()).round(1)
    result[cats == "moderate"] = np.random.uniform(6, 19.9, (cats == "moderate").sum()).round(1)
    result[cats == "fresh"]    = np.random.uniform(0.5, 5.9, (cats == "fresh").sum()).round(1)
    return result

# Base patient demographics
age   = np.random.randint(18, 95, N)
gender = np.random.choice(["M", "F"], N, p=[0.55, 0.45])
units  = np.random.choice(CARE_UNITS, N, p=[0.25, 0.20, 0.10, 0.15, 0.10, 0.10, 0.10])
admits = np.random.choice(ADMIT_TYPES, N, p=[0.30, 0.20, 0.15, 0.15, 0.10, 0.10])
vent_h = np.random.randint(1, 72, N)

# Lab values (realistic ICU distributions)
creatinine = synthetic_lab(1.8, 1.5, N, 0.3, 15.0)
bun        = synthetic_lab(28, 20, N, 5, 120)
potassium  = synthetic_lab(4.1, 0.7, N, 2.5, 7.0)
sodium     = synthetic_lab(138, 5, N, 120, 160)
glucose    = synthetic_lab(145, 55, N, 50, 500)
platelets  = synthetic_lab(185, 110, N, 10, 800)
wbc        = synthetic_lab(11.5, 7, N, 0.5, 60)
hemoglobin = synthetic_lab(9.8, 2.2, N, 4, 18)
lactate    = synthetic_lab(2.8, 2.5, N, 0.3, 20)
pao2       = synthetic_lab(85, 30, N, 30, 200)
paco2      = synthetic_lab(42, 10, N, 20, 80)
ph         = synthetic_lab(7.37, 0.07, N, 7.0, 7.6)
bilirubin  = synthetic_lab(1.8, 2.5, N, 0.1, 25)

# Mortality model: logistic function of key risk factors
log_odds = (
    -4.5
    + 0.03 * (age - 60)
    + 0.15 * lactate
    - 0.02 * (pao2 - 85)
    + 0.08 * creatinine
    + 0.005 * bun
    + 0.02 * vent_h
)
prob_death = 1 / (1 + np.exp(-log_odds))
outcome_death = (np.random.random(N) < prob_death).astype(int)

# Build DataFrame
df = pd.DataFrame({
    "stay_id":           np.arange(10000001, 10000001 + N),
    "subject_id":        np.arange(20000001, 20000001 + N),
    "hadm_id":           np.arange(30000001, 30000001 + N),
    "age":               age,
    "gender":            gender,
    "first_careunit":    units,
    "admission_type":    admits,
    "vent_duration_hours": vent_h,
    "outcome_death":     outcome_death,
    "creatinine_val":    creatinine,
    "bun_val":           bun,
    "potassium_val":     potassium,
    "sodium_val":        sodium,
    "glucose_val":       glucose,
    "platelets_val":     platelets,
    "wbc_val":           wbc,
    "hemoglobin_val":    hemoglobin,
    "lactate_val":       lactate,
    "pao2_val":          pao2,
    "paco2_val":         paco2,
    "ph_val":            ph,
    "bilirubin_val":     bilirubin,
    "creatinine_staleness": synthetic_staleness(N, 0.10, 0.20, 0.30),
    "bun_staleness":        synthetic_staleness(N, 0.10, 0.20, 0.30),
    "potassium_staleness":  synthetic_staleness(N, 0.08, 0.18, 0.32),
    "sodium_staleness":     synthetic_staleness(N, 0.08, 0.18, 0.32),
    "glucose_staleness":    synthetic_staleness(N, 0.05, 0.15, 0.35),
    "platelets_staleness":  synthetic_staleness(N, 0.20, 0.25, 0.25),
    "wbc_staleness":        synthetic_staleness(N, 0.10, 0.20, 0.30),
    "hemoglobin_staleness": synthetic_staleness(N, 0.15, 0.25, 0.28),
    "lactate_staleness":    synthetic_staleness(N, 0.20, 0.30, 0.25),
    "pao2_staleness":       synthetic_staleness(N, 0.18, 0.28, 0.27),
    "paco2_staleness":      synthetic_staleness(N, 0.18, 0.28, 0.27),
    "ph_staleness":         synthetic_staleness(N, 0.18, 0.28, 0.27),
    "bilirubin_staleness":  synthetic_staleness(N, 0.25, 0.30, 0.25),
})

out_path = Path(__file__).parent.parent / "data" / "demo" / "demo_cohort.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_path, index=False)

mortality_rate = outcome_death.mean() * 100
print(f"Generated {N} synthetic patients")
print(f"Mortality rate: {mortality_rate:.1f}%")
print(f"Saved to: {out_path}")
