import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("Loading dataset...")
ts = pd.read_parquet("d:/ICU_Mortality_Prediction/prototype/timeseries_long.parquet")
df_out = pd.read_parquet("d:/ICU_Mortality_Prediction/prototype/patient_level_features.parquet")

vent_ids = set(ts[(ts.Parameter == "MechVent") & (ts.Value == 1)].RecordID.unique())
ts = ts[ts.RecordID.isin(vent_ids)].sort_values(["RecordID", "Parameter", "minutes"]).reset_index(drop=True)
df_out = df_out[df_out.RecordID.isin(vent_ids)].copy()

INTERMITTENT_LABS = ["Lactate", "PaO2", "PaCO2", "pH", "Creatinine", "BUN", "WBC", 
                     "Platelets", "HCO3", "Glucose", "Bilirubin", "TroponinT", "TroponinI", "ALP", "AST", "ALT"]

def generate_landmark_dataset(T):
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
    
    # 6h recent slope
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
    
    # Impute missing staleness with max staleness (never measured = T * 2)
    for p in ts.Parameter.unique():
        col = f"{p}_stale_h"
        if col in tbl.columns:
            tbl[col] = tbl[col].fillna(T * 2.0)
            
    return tbl

landmarks_to_test = [12, 24, 36]
all_results = []

for T in landmarks_to_test:
    print(f"\n==================== Landmark T = {T}h ====================")
    tbl = generate_landmark_dataset(T)
    tr = tbl[tbl.set.isin(["a", "b"])].copy()
    te = tbl[tbl.set == "c"].copy()
    
    # Define feature sets
    meta = ["RecordID", "set", "died", "SAPS-I"]
    base_cols = [c for c in tbl.columns if c not in meta and not c.endswith("_stale_h")]
    
    # Targeted staleness: only intermittent labs
    targeted_stale_cols = base_cols + [f"{l}_stale_h" for l in INTERMITTENT_LABS if f"{l}_stale_h" in tbl.columns]
    
    # Engineered clinical intent features:
    # 1. Is the lab fresh (< 4 hours old)?
    # 2. Lab urgency ratio = (last value / normal_median) * (1 / (1 + stale_h/6))
    for df in [tr, te]:
        for l in INTERMITTENT_LABS:
            if f"{l}_last" in df.columns and f"{l}_stale_h" in df.columns:
                df[f"{l}_is_fresh"] = (df[f"{l}_stale_h"] <= 4.0).astype(float)
                # Interaction: value weighted by recency
                df[f"{l}_recency_weighted"] = df[f"{l}_last"] / (1.0 + df[f"{l}_stale_h"] / 12.0)
                
    intent_cols = targeted_stale_cols + \
                  [f"{l}_is_fresh" for l in INTERMITTENT_LABS if f"{l}_is_fresh" in tr.columns] + \
                  [f"{l}_recency_weighted" for l in INTERMITTENT_LABS if f"{l}_recency_weighted" in tr.columns]

    models = {
        "LightGBM": lgb.LGBMClassifier(n_estimators=350, learning_rate=0.03, num_leaves=15, 
                                       subsample=0.8, colsample_bytree=0.6, random_state=42, verbose=-1),
        "XGBoost": xgb.XGBClassifier(n_estimators=300, learning_rate=0.03, max_depth=4, 
                                     subsample=0.8, colsample_bytree=0.6, random_state=42, eval_metric="logloss"),
        "CatBoost": CatBoostClassifier(iterations=350, learning_rate=0.04, depth=5, 
                                      random_seed=42, verbose=0),
        "RandomForest": make_pipeline(SimpleImputer(strategy="median"), 
                                     RandomForestClassifier(n_estimators=250, max_depth=10, random_state=42, n_jobs=-1)),
        "MLP_NeuralNet": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                      MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42, early_stopping=True)),
        "LogisticRegression": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                           LogisticRegression(max_iter=1000, C=0.05, random_state=42))
    }
    
    feature_experiments = [
        ("Without Staleness", base_cols),
        ("Targeted Lab Staleness", targeted_stale_cols),
        ("Staleness + Clinical Recency", intent_cols)
    ]
    
    for feat_name, cols in feature_experiments:
        for model_name, model in models.items():
            # Fit
            model.fit(tr[cols], tr.died)
            p = model.predict_proba(te[cols])[:, 1]
            
            auroc = roc_auc_score(te.died, p)
            auprc = average_precision_score(te.died, p)
            brier = brier_score_loss(te.died, p)
            
            all_results.append({
                "Landmark": f"T={T}h",
                "Model": model_name,
                "Feature_Set": feat_name,
                "AUROC": auroc,
                "AUPRC": auprc,
                "Brier": brier
            })

df_all = pd.DataFrame(all_results)
df_all.to_csv("C:/Users/kpvlo/.gemini/antigravity/brain/c275bfab-b738-40db-b68a-bdce0b01ca09/scratch/staleness_multimodel_results.csv", index=False)
print("\n=== SUMMARY OF RESULTS ===")
# Pivot table of AUROC
piv_auroc = df_all.pivot_table(index=["Landmark", "Model"], columns="Feature_Set", values="AUROC").round(4)
print(piv_auroc)

print("\n=== PIVOT TABLE OF AUPRC ===")
piv_auprc = df_all.pivot_table(index=["Landmark", "Model"], columns="Feature_Set", values="AUPRC").round(4)
print(piv_auprc)
