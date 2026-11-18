import os
import sys
import json

# Ensure UTF-8 output on Windows console
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print(" MIMIC-IV v3.1 Mechanically Ventilated ICU Mortality Benchmark")
print(" Evaluating Targeted Lab Staleness Framework (N = 23,367 Patients)")
print("=" * 70)

# 1. Load Data
data_path = r"D:\ICU_Mortality_Prediction\data\mimiciv\mimiciv_ventilated_cohort_24h.csv"
df = pd.read_csv(data_path)
print(f"Cohort loaded: {len(df):,} patients, {df.shape[1]} features.")
mortality_rate = df['outcome_death'].mean()
print(f"Total Deaths: {df['outcome_death'].sum():,} ({mortality_rate * 100:.2f}% mortality)\n")

# 2. Encode Categoricals
df['gender'] = (df['gender'] == 'M').astype(int)
df = pd.get_dummies(df, columns=['first_careunit', 'admission_type'], drop_first=True)

# 3. Define Feature Sets
base_demographics = ['age', 'gender', 'vent_duration_hours'] + [c for c in df.columns if c.startswith('first_careunit_') or c.startswith('admission_type_')]
lab_vals = [c for c in df.columns if c.endswith('_val')]
lab_stales = [c for c in df.columns if c.endswith('_staleness')]

features_no_staleness = base_demographics + lab_vals
features_with_staleness = base_demographics + lab_vals + lab_stales

print(f"Features without staleness (Baseline) : {len(features_no_staleness)}")
print(f"Features with Targeted Staleness      : {len(features_with_staleness)}")

y = df['outcome_death'].values

# 4. Stratified 5-Fold Cross-Validation Setup
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models_to_test = {
    "LightGBM": lgb.LGBMClassifier(n_estimators=300, max_depth=6, learning_rate=0.03, random_state=42, verbose=-1),
    "XGBoost": xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.03, random_state=42, eval_metric="logloss"),
    "CatBoost": CatBoostClassifier(iterations=300, depth=6, learning_rate=0.03, random_seed=42, verbose=0),
    "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1),
    "LogisticRegression": make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(max_iter=1000, C=0.1, random_state=42))
}

results = []
oof_preds = {}

for model_name, model in models_to_test.items():
    print(f"\nEvaluating {model_name}...")
    
    # Track OOF predictions for both variants
    preds_base = np.zeros(len(df))
    preds_stale = np.zeros(len(df))
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(df, y)):
        X_tr_base, y_tr = df.loc[train_idx, features_no_staleness], y[train_idx]
        X_va_base, y_va = df.loc[val_idx, features_no_staleness], y[val_idx]
        
        X_tr_stale = df.loc[train_idx, features_with_staleness]
        X_va_stale = df.loc[val_idx, features_with_staleness]
        
        # Train baseline
        m_base = model
        m_base.fit(X_tr_base, y_tr)
        preds_base[val_idx] = m_base.predict_proba(X_va_base)[:, 1]
        
        # Train with staleness
        m_stale = model
        m_stale.fit(X_tr_stale, y_tr)
        preds_stale[val_idx] = m_stale.predict_proba(X_va_stale)[:, 1]

    oof_preds[f"{model_name}_base"] = preds_base
    oof_preds[f"{model_name}_stale"] = preds_stale

    # Metrics Baseline
    auroc_base = roc_auc_score(y, preds_base)
    auprc_base = average_precision_score(y, preds_base)
    brier_base = brier_score_loss(y, preds_base)

    # Metrics Staleness
    auroc_stale = roc_auc_score(y, preds_stale)
    auprc_stale = average_precision_score(y, preds_stale)
    brier_stale = brier_score_loss(y, preds_stale)

    diff_auprc = auprc_stale - auprc_base
    diff_auroc = auroc_stale - auroc_base

    print(f"  [Baseline]  AUROC: {auroc_base:.4f} | AUPRC: {auprc_base:.4f} | Brier: {brier_base:.4f}")
    print(f"  [Staleness] AUROC: {auroc_stale:.4f} | AUPRC: {auprc_stale:.4f} | Brier: {brier_stale:.4f}")
    print(f"  >>> Gain: Delta_AUPRC = {diff_auprc*100:+.2f}% | Delta_AUROC = {diff_auroc*100:+.2f}%")

    results.append({
        "Model": model_name,
        "AUROC_Baseline": auroc_base,
        "AUROC_Staleness": auroc_stale,
        "Delta_AUROC_pct": diff_auroc * 100,
        "AUPRC_Baseline": auprc_base,
        "AUPRC_Staleness": auprc_stale,
        "Delta_AUPRC_pct": diff_auprc * 100,
        "Brier_Baseline": brier_base,
        "Brier_Staleness": brier_stale
    })

# 5. Bootstrap Hypothesis Testing (XGBoost)
print("\n" + "=" * 70)
print(" Running 1,000-fold Paired Patient Bootstrap on XGBoost...")
print("=" * 70)

np.random.seed(42)
n_bootstraps = 1000
boot_diffs_auprc = []
boot_diffs_auroc = []
N = len(y)

xgb_base = oof_preds["XGBoost_base"]
xgb_stale = oof_preds["XGBoost_stale"]

for i in range(n_bootstraps):
    sample_idx = np.random.randint(0, N, N)
    y_s = y[sample_idx]
    if len(np.unique(y_s)) < 2:
        continue
    
    auprc_s_base = average_precision_score(y_s, xgb_base[sample_idx])
    auprc_s_stale = average_precision_score(y_s, xgb_stale[sample_idx])
    boot_diffs_auprc.append(auprc_s_stale - auprc_s_base)

    auroc_s_base = roc_auc_score(y_s, xgb_base[sample_idx])
    auroc_s_stale = roc_auc_score(y_s, xgb_stale[sample_idx])
    boot_diffs_auroc.append(auroc_s_stale - auroc_s_base)

boot_diffs_auprc = np.array(boot_diffs_auprc)
boot_diffs_auroc = np.array(boot_diffs_auroc)

p_val_auprc = np.mean(boot_diffs_auprc <= 0)
ci_auprc = np.percentile(boot_diffs_auprc, [2.5, 97.5])
ci_auroc = np.percentile(boot_diffs_auroc, [2.5, 97.5])

print(f"Paired Bootstrap P-Value (AUPRC Gain > 0): p = {p_val_auprc:.4f}")
print(f"95% CI for Delta_AUPRC: [{ci_auprc[0]*100:.3f}%, {ci_auprc[1]*100:.3f}%]")
print(f"95% CI for Delta_AUROC: [{ci_auroc[0]*100:.3f}%, {ci_auroc[1]*100:.3f}%]")

# 6. Save results
out_dir = r"D:\ICU_Mortality_Prediction\results\tables"
os.makedirs(out_dir, exist_ok=True)
df_results = pd.DataFrame(results)
res_file = os.path.join(out_dir, "mimiciv_staleness_benchmark_results.csv")
df_results.to_csv(res_file, index=False)
print(f"\nSaved benchmark results to: {res_file}")

stats_file = r"D:\ICU_Mortality_Prediction\results\stats\mimiciv_bootstrap_stats.json"
os.makedirs(os.path.dirname(stats_file), exist_ok=True)
stats_payload = {
    "cohort_size": int(len(df)),
    "deaths": int(df['outcome_death'].sum()),
    "mortality_rate": float(mortality_rate),
    "p_value_auprc": float(p_val_auprc),
    "ci_auprc_95_low": float(ci_auprc[0]),
    "ci_auprc_95_high": float(ci_auprc[1]),
    "ci_auroc_95_low": float(ci_auroc[0]),
    "ci_auroc_95_high": float(ci_auroc[1]),
}
with open(stats_file, "w") as f:
    json.dump(stats_payload, f, indent=2)
print(f"Saved bootstrap statistics to: {stats_file}")

print("=" * 70)
print(" BENCHMARK COMPLETED SUCCESSFULLY!")
print("=" * 70)
