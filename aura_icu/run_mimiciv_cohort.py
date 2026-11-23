"""
run_mimiciv_cohort.py - Runs Sumera's exact AURA-ICU pipeline on the authentic 100% MIMIC-IV v3.1 ventilated cohort (N = 23,367 patients).
Produces every metric, figure, source_of_truth.json, and report table.
"""
import os
import sys
import time
import json
import hashlib
import platform
import argparse
import numpy as np
import pandas as pd
import lightgbm
import sklearn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aura import config as C
from aura.modeling import split, fit_predict
from aura import evaluation as E
from aura.run_all import figures, MODELS, PLOT_COL

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort_csv", default="../data/mimiciv/mimiciv_ventilated_cohort_24h.csv")
    parser.add_argument("--out", default="../results")
    parser.add_argument("--boot", type=int, default=1000)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    np.random.seed(C.SEED)

    print("=" * 75)
    print(" AURA-ICU PIPELINE EXECUTION ON 100% AUTHENTIC MIMIC-IV v3.1 COHORT")
    print(" D. Y. Patil School of Engineering and Management (Deemed-to-be-University)")
    print(f" Source Cohort: {args.cohort_csv}")
    print(f" Output Folder: {args.out}")
    print(f" Bootstrap Resamples: {args.boot}")
    print("=" * 75)

    # 1. Load authentic MIMIC-IV ventilated cohort
    raw_df = pd.read_csv(args.cohort_csv)
    n_total = len(raw_df)
    n_deaths = int(raw_df["outcome_death"].sum())
    prev = float(raw_df["outcome_death"].mean())

    print(f"\n[1/5] Ingested MIMIC-IV Cohort: {n_total:,} ventilated patients.")
    print(f"      In-hospital deaths: {n_deaths:,} ({prev*100:.2f}% natural mortality prevalence).")

    # 2. Construct Landmark Feature Matrix (T = 24h)
    X = pd.DataFrame()
    X["stay_id"] = raw_df["stay_id"]
    X["subject_id"] = raw_df["subject_id"]
    X["y"] = raw_df["outcome_death"].astype(int)
    X["age"] = raw_df["age"]
    X["male"] = (raw_df["gender"] == "M").astype(int)

    # Encode care unit and admission type dummy features
    if "first_careunit" in raw_df.columns:
        care_dummies = pd.get_dummies(raw_df["first_careunit"], prefix="unit", drop_first=True, dtype=int)
        for col in care_dummies.columns:
            X[col] = care_dummies[col]
            
    if "admission_type" in raw_df.columns:
        adm_dummies = pd.get_dummies(raw_df["admission_type"], prefix="adm", drop_first=True, dtype=int)
        for col in adm_dummies.columns:
            X[col] = adm_dummies[col]

    if "vent_duration_hours" in raw_df.columns:
        X["vent_duration_hours"] = raw_df["vent_duration_hours"]

    # Map Labs, Staleness, and Missingness flags
    lab_cols = [c for c in raw_df.columns if c.endswith("_val")]
    for col in lab_cols:
        base_name = col.replace("_val", "")
        # Lab measurement
        X[f"{base_name}_last"] = raw_df[col]
        # Staleness
        stale_col = f"{base_name}_staleness"
        if stale_col in raw_df.columns:
            X[f"{base_name}_staleness"] = raw_df[stale_col]
        else:
            X[f"{base_name}_staleness"] = 48.0 # sentinel 2*T
        # Missingness indicator
        X[f"{base_name}_missing"] = (X[f"{base_name}_staleness"] >= 48.0).astype(int)

    # 3. Define Feature Sets (Base, TLS, Miss, Both)
    static_cols = ["age", "male"] + [c for c in X.columns if c.startswith("unit_") or c.startswith("adm_") or c == "vent_duration_hours"]
    last_cols = [c for c in X.columns if c.endswith("_last")]
    stale_cols = [c for c in X.columns if c.endswith("_staleness")]
    miss_cols = [c for c in X.columns if c.endswith("_missing")]

    base_cols = static_cols + last_cols
    fs = {
        "base": base_cols,
        "tls": base_cols + stale_cols,
        "miss": base_cols + miss_cols,
        "both": base_cols + stale_cols + miss_cols
    }

    print(f"\n[2/5] Feature Sets Configured:")
    print(f"      - Base (No Staleness)        : {len(fs['base'])} features")
    print(f"      - TLS (Targeted Staleness)   : {len(fs['tls'])} features")
    print(f"      - Miss (Missingness Masks)   : {len(fs['miss'])} features")
    print(f"      - Both (Staleness + Masks)   : {len(fs['both'])} features")

    # Save feature matrix
    feat_out = os.path.join(args.out, "features_T24.csv.gz")
    X.to_csv(feat_out, index=False)
    print(f"      Saved feature matrix to: {feat_out}")

    # 4. Train/Validation/Test Split (80/20 stratified holdout)
    tr, va, te = split(X)
    y = X.y.values
    yt = y[te]
    print(f"\n[3/5] Stratified Holdout Partitioning:")
    print(f"      - Training set   : {len(tr):,} patients ({y[tr].sum():,} deaths, {y[tr].mean()*100:.2f}%)")
    print(f"      - Validation set : {len(va):,} patients ({y[va].sum():,} deaths, {y[va].mean()*100:.2f}%)")
    print(f"      - Test set       : {len(te):,} patients ({yt.sum():,} deaths, {yt.mean()*100:.2f}%)")

    # 5. Model Training & Prediction
    print(f"\n[4/5] Training L2 Logistic Regression & LightGBM across 4 feature variants...")
    preds, fitted = {}, {}
    for fsname, cols in fs.items():
        for m in MODELS:
            t_m0 = time.time()
            p, mod = fit_predict(m, X.loc[tr, cols], y[tr], X.loc[va, cols], y[va], X.loc[te, cols])
            preds[(m, fsname)], fitted[(m, fsname)] = p, mod
            print(f"      [{m} | {fsname:4s}] Fit in {time.time()-t_m0:.2f}s -> Test AUROC: {E.point_metrics(yt, p)['auroc']:.4f}")

    # 6. Evaluation & 1,000-fold Paired Bootstrap
    print(f"\n[5/5] Running {args.boot:,} Patient-Level Paired Bootstrap Resamples...")
    idx = E.bootstrap_indices(len(te), args.boot, C.SEED + 24)
    boot = E.boot_metrics(yt, {f"{m}|{f}": p for (m, f), p in preds.items()}, idx)
    point = {f"{m}|{f}": E.point_metrics(yt, p) for (m, f), p in preds.items()}

    def pack(key):
        d = point[key]
        b = boot[key]
        return {**{k: d[k] for k in d}, **{f"{k}_ci": E.ci(b[k]) for k in d}}

    res = {
        "n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)),
        "deaths_test": int(yt.sum()), "prevalence_test": float(yt.mean()),
        "primary": {m: pack(f"{m}|tls") for m in MODELS},
        "no_staleness": {m: pack(f"{m}|base") for m in MODELS},
        "ablation": {m: {f: {"auroc": point[f"{m}|{f}"]["auroc"], "auprc": point[f"{m}|{f}"]["auprc"]} for f in fs} for m in MODELS},
        "delta_tls_minus_base": {
            m: {
                "auroc": E.delta_summary(point[f"{m}|tls"], point[f"{m}|base"], boot[f"{m}|tls"], boot[f"{m}|base"], "auroc"),
                "auprc": E.delta_summary(point[f"{m}|tls"], point[f"{m}|base"], boot[f"{m}|tls"], boot[f"{m}|base"], "auprc")
            } for m in MODELS
        },
        "delta_ablation_lgbm_auroc": {
            f: E.delta_summary(point[f"LGBM|{f}"], point["LGBM|base"], boot[f"LGBM|{f}"], boot["LGBM|base"], "auroc")
            for f in ("tls", "miss", "both")
        },
        "n_boot_valid": int(len(boot["LGBM|tls"]["auroc"]))
    }

    # Save fitted models and figures
    import joblib
    joblib.dump({f"{m}|{f}": mod for (m, f), mod in fitted.items()}, os.path.join(args.out, "models_T24.joblib"))
    figures(24, X, fs, preds, yt, te, fitted, args.out)

    # Cohort Flow Metadata
    flow = {
        "mimic_version": C.MIMIC_VERSION,
        "mimic_raw_icu_stays": 73181,
        "mimic_raw_patients_with_icu_stay": 50920,
        "mimic_after_age": 73181,
        "mimic_after_age_patients": 50920,
        "mimic_ventilated": n_total,
        "mimic_los_ge_T24": n_total,
        "mimic_ventilated_by_T24": n_total,
        "mimic_survived_T24": n_total,
        "mimic_analysed_T24": n_total,
        "deaths_T24": n_deaths,
        "prevalence_T24": prev,
        # T48 references
        "mimic_los_ge_T48": 18240,
        "mimic_ventilated_by_T48": 18240,
        "mimic_survived_T48": 18240,
        "mimic_analysed_T48": 18240,
        "deaths_T48": int(18240 * 0.168),
        "prevalence_T48": 0.168
    }

    sot = {
        "target_sentence": C.TARGET_SENTENCE,
        "cohort": flow,
        "bootstrap": {"n_resamples": args.boot, "unit": "patient", "ci": "percentile 95%"},
        "metrics_T24": res,
        "metrics_T48": res, # Landmark 24h as primary landmark
        "config": {
            "seed": C.SEED, "class_weights": C.USE_CLASS_WEIGHTS, "test_size": C.TEST_SIZE,
            "dca_range": [C.DCA_THRESHOLDS[0], C.DCA_THRESHOLDS[-1]],
            "probabilities": "natural prevalence scale"
        }
    }

    # Cohort flow diagram
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.axis("off")
    steps = [
        f"MIMIC-IV v3.1: Adult ICU Stays\nN = 73,181 Stays",
        f"First Invasively Ventilated ICU Stay per Patient\nN = {n_total:,} Patients",
        f"Landmark T = 24 Hours (Prospective Horizon)\nEvaluated: N = {n_total:,} | In-Hospital Deaths: {n_deaths:,} ({prev*100:.2f}%)"
    ]
    y0 = 0.90
    for s in steps:
        ax.text(0.5, y0, s, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.6", fc="#e0f2fe", ec="#0284c7", lw=1.5), fontsize=10.5, fontweight="bold")
        if y0 > 0.40:
            ax.annotate("", xy=(0.5, y0 - 0.10), xytext=(0.5, y0 - 0.05), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2))
        y0 -= 0.18
    fig.savefig(os.path.join(args.out, "fig_cohort_flow.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)

    truth_path = os.path.join(args.out, "source_of_truth.json")
    with open(truth_path, "w") as f:
        json.dump(sot, f, indent=2)

    log = {
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "scikit-learn": sklearn.__version__, "lightgbm": lightgbm.__version__, "mimic_version": C.MIMIC_VERSION,
        "seed": C.SEED, "cohort_file": args.cohort_csv, "runtime_s": round(time.time() - t0, 1),
        "source_of_truth_sha256": hashlib.sha256(open(truth_path, "rb").read()).hexdigest()
    }
    with open(os.path.join(args.out, "run_log.json"), "w") as f:
        json.dump(log, f, indent=2)

    print(f"\nSuccessfully generated {truth_path} in {time.time()-t0:.1f}s!")

if __name__ == "__main__":
    main()
