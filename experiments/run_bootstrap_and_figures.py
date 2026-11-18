import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, average_precision_score, brier_score_loss
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
import os
import json

print("Loading data for publication figures and statistical testing...")
ts = pd.read_parquet("d:/ICU_Mortality_Prediction/prototype/timeseries_long.parquet")
df_out = pd.read_parquet("d:/ICU_Mortality_Prediction/prototype/patient_level_features.parquet")

vent_ids = set(ts[(ts.Parameter == "MechVent") & (ts.Value == 1)].RecordID.unique())
ts = ts[ts.RecordID.isin(vent_ids)].sort_values(["RecordID", "Parameter", "minutes"]).reset_index(drop=True)
df_out = df_out[df_out.RecordID.isin(vent_ids)].copy()

INTERMITTENT_LABS = ["Lactate", "PaO2", "PaCO2", "pH", "Creatinine", "BUN", "WBC", 
                     "Platelets", "HCO3", "Glucose", "Bilirubin", "TroponinT", "TroponinI", "ALP", "AST", "ALT"]

def get_landmark_data(T=36):
    d = ts[ts.minutes <= T * 60]
    g = d.groupby(["RecordID", "Parameter"])
    
    a = g.agg(
        last=("Value", "last"),
        mean=("Value", "mean"),
        mn=("Value", "min"),
        mx=("Value", "max"),
        n=("Value", "size"),
        t_last=("minutes", "max")
    )
    a["stale_h"] = T - a.t_last / 60
    
    w = (d[d.minutes > (T - 6) * 60].groupby(["RecordID", "Parameter"])
           .agg(w_first=("Value", "first"), w_last=("Value", "last"),
                t0=("minutes", "min"), t1=("minutes", "max"), w_mean=("Value", "mean")))
    w["slope6"] = (w.w_last - w.w_first) / ((w.t1 - w.t0) / 60).where(w.t1 > w.t0)
    
    f = a.drop(columns="t_last").join(w[["slope6", "w_mean"]]).unstack("Parameter")
    f.columns = [f"{p}_{s}" for s, p in f.columns]
    f = f.reset_index()
    
    cohort = df_out.loc[df_out.Length_of_stay >= T / 24,
                        ["RecordID", "set", "died", "SAPS-I", "Age", "Gender", "ICUType", "Weight"]]
    tbl = cohort.merge(f, on="RecordID", how="left")
    n_cols = [c for c in tbl.columns if c.endswith("_n")]
    tbl[n_cols] = tbl[n_cols].fillna(0)
    
    for p in ts.Parameter.unique():
        col = f"{p}_stale_h"
        if col in tbl.columns:
            tbl[col] = tbl[col].fillna(T * 2.0)
            
    return tbl

print("Building features for T=36h...")
tbl36 = get_landmark_data(36)

tr = tbl36[tbl36.set.isin(["a", "b"])].copy()
te = tbl36[tbl36.set == "c"].copy()

meta = ["RecordID", "set", "died", "SAPS-I"]
base_cols = [c for c in tbl36.columns if c not in meta and not c.endswith("_stale_h")]
target_cols = base_cols + [f"{l}_stale_h" for l in INTERMITTENT_LABS if f"{l}_stale_h" in tbl36.columns]

print("Training baseline XGBoost (without staleness)...")
m_base = xgb.XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=4, 
                           subsample=0.8, colsample_bytree=0.6, random_state=42, eval_metric="logloss")
m_base.fit(tr[base_cols], tr.died)
p_base = m_base.predict_proba(te[base_cols])[:, 1]

print("Training targeted staleness XGBoost...")
m_target = xgb.XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=4, 
                             subsample=0.8, colsample_bytree=0.6, random_state=42, eval_metric="logloss")
m_target.fit(tr[target_cols], tr.died)
p_target = m_target.predict_proba(te[target_cols])[:, 1]

y_true = te.died.values

# 1. Statistical Significance: 1000-fold Paired Patient Bootstrap
print("\nRunning 1,000-fold Paired Bootstrap...")
rng = np.random.default_rng(42)
n_samples = len(y_true)
boot_auc_diff = []
boot_pr_diff = []
boot_brier_diff = []

for _ in range(1000):
    idx = rng.choice(n_samples, size=n_samples, replace=True)
    y_b = y_true[idx]
    pb_b = p_base[idx]
    pt_b = p_target[idx]
    
    # Differences
    auc_diff = roc_auc_score(y_b, pt_b) - roc_auc_score(y_b, pb_b)
    pr_diff = average_precision_score(y_b, pt_b) - average_precision_score(y_b, pb_b)
    brier_diff = brier_score_loss(y_b, pt_b) - brier_score_loss(y_b, pb_b)
    
    boot_auc_diff.append(auc_diff)
    boot_pr_diff.append(pr_diff)
    boot_brier_diff.append(brier_diff)

boot_auc_diff = np.array(boot_auc_diff)
boot_pr_diff = np.array(boot_pr_diff)
boot_brier_diff = np.array(boot_brier_diff)

# Confidence intervals (95%)
auc_ci = (np.percentile(boot_auc_diff, 2.5), np.percentile(boot_auc_diff, 97.5))
pr_ci = (np.percentile(boot_pr_diff, 2.5), np.percentile(boot_pr_diff, 97.5))
brier_ci = (np.percentile(boot_brier_diff, 2.5), np.percentile(boot_brier_diff, 97.5))

# One-tailed and two-tailed p-values for AUPRC improvement
p_val_pr = np.mean(boot_pr_diff <= 0)
p_val_auc = np.mean(boot_auc_diff <= 0)

stats_summary = {
    "Baseline_AUROC": float(roc_auc_score(y_true, p_base)),
    "Targeted_AUROC": float(roc_auc_score(y_true, p_target)),
    "Delta_AUROC": float(np.mean(boot_auc_diff)),
    "AUROC_95_CI": [float(auc_ci[0]), float(auc_ci[1])],
    "AUROC_p_value": float(p_val_auc),
    
    "Baseline_AUPRC": float(average_precision_score(y_true, p_base)),
    "Targeted_AUPRC": float(average_precision_score(y_true, p_target)),
    "Delta_AUPRC": float(np.mean(boot_pr_diff)),
    "AUPRC_95_CI": [float(pr_ci[0]), float(pr_ci[1])],
    "AUPRC_p_value": float(p_val_pr),
    
    "Baseline_Brier": float(brier_score_loss(y_true, p_base)),
    "Targeted_Brier": float(brier_score_loss(y_true, p_target)),
    "Delta_Brier": float(np.mean(boot_brier_diff))
}

print("\n================ STATISTICAL RESULTS ================")
print(f"AUROC: Baseline={stats_summary['Baseline_AUROC']:.4f}, Targeted={stats_summary['Targeted_AUROC']:.4f}, Delta={stats_summary['Delta_AUROC']:+.4f} (95% CI [{auc_ci[0]:+.4f}, {auc_ci[1]:+.4f}], p={p_val_auc:.4f})")
print(f"AUPRC: Baseline={stats_summary['Baseline_AUPRC']:.4f}, Targeted={stats_summary['Targeted_AUPRC']:.4f}, Delta={stats_summary['Delta_AUPRC']:+.4f} (95% CI [{pr_ci[0]:+.4f}, {pr_ci[1]:+.4f}], p={p_val_pr:.4f})")
print(f"Brier Loss: Baseline={stats_summary['Baseline_Brier']:.4f}, Targeted={stats_summary['Targeted_Brier']:.4f}, Delta={stats_summary['Delta_Brier']:+.4f}")

with open("C:/Users/kpvlo/.gemini/antigravity/brain/c275bfab-b738-40db-b68a-bdce0b01ca09/scratch/bootstrap_stats.json", "w") as f:
    json.dump(stats_summary, f, indent=2)

# 2. Publication-Ready Figure Generation
print("\nGenerating Publication Figures...")
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)

# Colors
c_base = "#718096"
c_target = "#2B6CB0"

# Panel A: ROC Curves
fpr_b, tpr_b, _ = roc_curve(y_true, p_base)
fpr_t, tpr_t, _ = roc_curve(y_true, p_target)

axes[0].plot(fpr_b, tpr_b, color=c_base, linestyle="--", lw=2, label=f"Baseline (AUC = {stats_summary['Baseline_AUROC']:.3f})")
axes[0].plot(fpr_t, tpr_t, color=c_target, lw=2.5, label=f"Targeted Staleness (AUC = {stats_summary['Targeted_AUROC']:.3f})")
axes[0].plot([0, 1], [0, 1], "k:", alpha=0.4)
axes[0].set_title("(A) Receiver Operating Characteristic (ROC)", fontsize=12, fontweight="bold", pad=10)
axes[0].set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
axes[0].set_ylabel("True Positive Rate (Sensitivity)", fontsize=11)
axes[0].legend(loc="lower right", frameon=True, fontsize=10)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1.02])

# Panel B: Precision-Recall Curves
pre_b, rec_b, _ = precision_recall_curve(y_true, p_base)
pre_t, rec_t, _ = precision_recall_curve(y_true, p_target)
prevalence = np.mean(y_true)

axes[1].plot(rec_b, pre_b, color=c_base, linestyle="--", lw=2, label=f"Baseline (AUPRC = {stats_summary['Baseline_AUPRC']:.3f})")
axes[1].plot(rec_t, pre_t, color="#C53030", lw=2.5, label=f"Targeted Staleness (AUPRC = {stats_summary['Targeted_AUPRC']:.3f})")
axes[1].axhline(prevalence, color="gray", linestyle=":", alpha=0.5, label=f"No-Skill Baseline ({prevalence:.2f})")
axes[1].set_title("(B) Precision-Recall Curve (P-R)", fontsize=12, fontweight="bold", pad=10)
axes[1].set_xlabel("Recall (Sensitivity)", fontsize=11)
axes[1].set_ylabel("Precision (Positive Predictive Value)", fontsize=11)
axes[1].legend(loc="upper right", frameon=True, fontsize=10)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1.02])

# Panel C: Calibration Curves
prob_true_b, prob_pred_b = calibration_curve(y_true, p_base, n_bins=8, strategy="quantile")
prob_true_t, prob_pred_t = calibration_curve(y_true, p_target, n_bins=8, strategy="quantile")

axes[2].plot([0, 0.6], [0, 0.6], "k:", alpha=0.6, label="Perfect Calibration")
axes[2].plot(prob_pred_b, prob_true_b, "s--", color=c_base, lw=1.8, ms=6, label=f"Baseline (Brier = {stats_summary['Baseline_Brier']:.3f})")
axes[2].plot(prob_pred_t, prob_true_t, "o-", color="#2F855A", lw=2.2, ms=7, label=f"Targeted Staleness (Brier = {stats_summary['Targeted_Brier']:.3f})")
axes[2].set_title("(C) Reliability Diagram (Calibration Curve)", fontsize=12, fontweight="bold", pad=10)
axes[2].set_xlabel("Mean Predicted Mortality Risk", fontsize=11)
axes[2].set_ylabel("Empirical Observed Fraction", fontsize=11)
axes[2].legend(loc="upper left", frameon=True, fontsize=10)
axes[2].set_xlim([0, 0.65])
axes[2].set_ylim([0, 0.65])

plt.suptitle("Impact of Observation Staleness on Dynamic ICU Mortality Prediction (Landmark T = 36h)", 
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()

# Save in Downloads & scratch
out_downloads = "C:/Users/kpvlo/Downloads/Figure1_Staleness_Performance_Curves.png"
out_scratch = "C:/Users/kpvlo/.gemini/antigravity/brain/c275bfab-b738-40db-b68a-bdce0b01ca09/scratch/Figure1_Staleness_Performance_Curves.png"

plt.savefig(out_downloads, dpi=300, bbox_inches="tight")
plt.savefig(out_scratch, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nFigure successfully generated and saved to:\n1. {out_downloads}\n2. {out_scratch}")
