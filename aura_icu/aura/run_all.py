"""One command regenerates every number, table and figure in the report.
   python -m aura.run_all --data /path/to/mimiciv --out results
"""
import argparse, hashlib, json, os, platform, sys, time, warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*eval_set.*")
import joblib, lightgbm, numpy as np, pandas as pd, sklearn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import config as C
from .cohort import build_cohort
from .features import load_events, build_features, feature_sets
from .modeling import split, fit_predict
from . import evaluation as E

MODELS = ["LR", "LGBM"]
PLOT_COL = {"LR": "#1f77b4", "LGBM": "#d62728"}


def analyse_horizon(T, stays, vit, lab, out, B):
    X = build_features(stays, vit, lab, T)
    X.to_csv(f"{out}/features_T{T}.csv.gz", index=False)
    fs = feature_sets(X)
    tr, va, te = split(X)
    y = X.y.values
    preds, fitted = {}, {}
    for fsname, cols in fs.items():
        for m in MODELS:
            p, mod = fit_predict(m, X.loc[tr, cols], y[tr], X.loc[va, cols], y[va], X.loc[te, cols])
            preds[(m, fsname)], fitted[(m, fsname)] = p, mod
    yt = y[te]
    idx = E.bootstrap_indices(len(te), B, C.SEED + T)
    boot = E.boot_metrics(yt, {f"{m}|{f}": p for (m, f), p in preds.items()}, idx)
    point = {f"{m}|{f}": E.point_metrics(yt, p) for (m, f), p in preds.items()}

    def pack(key):
        d = point[key]; b = boot[key]
        return {**{k: d[k] for k in d}, **{f"{k}_ci": E.ci(b[k]) for k in d}}

    res = {"n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)),
           "deaths_test": int(yt.sum()), "prevalence_test": float(yt.mean())}
    res["primary"] = {m: pack(f"{m}|tls") for m in MODELS}              # TLS feature set
    res["no_staleness"] = {m: pack(f"{m}|base") for m in MODELS}
    res["ablation"] = {m: {f: {"auroc": point[f"{m}|{f}"]["auroc"], "auprc": point[f"{m}|{f}"]["auprc"]}
                           for f in fs} for m in MODELS}
    res["delta_tls_minus_base"] = {
        m: {"auroc": E.delta_summary(point[f"{m}|tls"], point[f"{m}|base"], boot[f"{m}|tls"], boot[f"{m}|base"], "auroc"),
            "auprc": E.delta_summary(point[f"{m}|tls"], point[f"{m}|base"], boot[f"{m}|tls"], boot[f"{m}|base"], "auprc")}
        for m in MODELS}
    res["delta_ablation_lgbm_auroc"] = {
        f: E.delta_summary(point[f"LGBM|{f}"], point["LGBM|base"], boot[f"LGBM|{f}"], boot["LGBM|base"], "auroc")
        for f in ("tls", "miss", "both")}
    res["n_boot_valid"] = int(len(boot["LGBM|tls"]["auroc"]))

    joblib.dump({f"{m}|{f}": mod for (m, f), mod in fitted.items()}, f"{out}/models_T{T}.joblib")
    figures(T, X, fs, preds, yt, te, fitted, out)
    return res


def figures(T, X, fs, preds, yt, te, fitted, out):
    from sklearn.metrics import roc_curve
    th = C.DCA_THRESHOLDS
    # ROC
    fig, ax = plt.subplots(figsize=(5, 5))
    for m in MODELS:
        fpr, tpr, _ = roc_curve(yt, preds[(m, "tls")]); ax.plot(fpr, tpr, color=PLOT_COL[m], label=m)
    ax.plot([0, 1], [0, 1], "k:"); ax.set(xlabel="1 - Specificity", ylabel="Sensitivity", title=f"ROC, T = {T} h"); ax.legend()
    fig.savefig(f"{out}/fig_roc_T{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # Calibration (decile bins + lowess)
    from statsmodels.nonparametric.smoothers_lowess import lowess
    fig, ax = plt.subplots(figsize=(5, 5))
    for m in MODELS:
        p = preds[(m, "tls")]
        d = pd.DataFrame({"p": p, "y": yt}); d["bin"] = pd.qcut(d.p, 10, duplicates="drop")
        g = d.groupby("bin", observed=True).agg(p=("p", "mean"), y=("y", "mean"))
        ax.plot(g.p, g.y, "o", color=PLOT_COL[m], label=f"{m} (deciles)")
        lw = lowess(yt.astype(float), p, frac=0.5, it=0); ax.plot(lw[:, 0], lw[:, 1], color=PLOT_COL[m], lw=1)
    mx = max(0.05, float(max(preds[(m, 'tls')].max() for m in MODELS)))
    ax.plot([0, mx], [0, mx], "k:"); ax.set(xlabel="Predicted probability", ylabel="Observed proportion", title=f"Calibration, T = {T} h"); ax.legend()
    fig.savefig(f"{out}/fig_calibration_T{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # DCA
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for m in MODELS:
        ax.plot(th, E.net_benefit(yt, preds[(m, "tls")], th), color=PLOT_COL[m], label=m)
    ax.plot(th, E.treat_all(yt, th), "gray", label="Treat all"); ax.axhline(0, color="k", lw=0.8, label="Treat none")
    ax.set(xlabel="Threshold probability", ylabel="Net benefit", title=f"Decision curve, T = {T} h"); ax.legend()
    ax.set_ylim(-0.05, max(0.05, E.treat_all(yt, th)[0] * 1.1))
    fig.savefig(f"{out}/fig_dca_T{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    # LightGBM importance via built-in SHAP-style contributions (pred_contrib)
    cols = fs["tls"]; mod = fitted[("LGBM", "tls")]
    contrib = mod.booster_.predict(X.loc[te, cols], pred_contrib=True)[:, :-1]
    imp = pd.Series(np.abs(contrib).mean(0), index=cols).sort_values().tail(15)
    imp.to_csv(f"{out}/shap_importance_T{T}.csv")
    fig, ax = plt.subplots(figsize=(6, 5)); imp.plot.barh(ax=ax, color="#d62728")
    ax.set(xlabel="Mean |SHAP value| (log-odds)", title=f"LightGBM feature importance, T = {T} h")
    fig.savefig(f"{out}/fig_shap_T{T}.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def flow_figure(flow, out):
    fig, ax = plt.subplots(figsize=(8, 9)); ax.axis("off")
    steps = [f"MIMIC-IV {flow['mimic_version']}: ICU stays\nn = {flow['mimic_raw_icu_stays']}",
             f"Adults (age >= 18)\nn = {flow['mimic_after_age']}",
             f"First invasively ventilated ICU stay per patient\nn = {flow['mimic_ventilated']}"]
    for T, x in zip(C.HORIZONS, (0.25, 0.75)):
        pass
    y0 = 0.93
    for s in steps:
        ax.text(0.5, y0, s, ha="center", va="center", bbox=dict(boxstyle="round", fc="#eef"), transform=ax.transAxes)
        ax.annotate("", xy=(0.5, y0 - 0.075), xytext=(0.5, y0 - 0.035), xycoords="axes fraction", arrowprops=dict(arrowstyle="->"))
        y0 -= 0.12
    for T, x in zip(C.HORIZONS, (0.27, 0.73)):
        txt = (f"T = {T} h\nICU LOS >= T: {flow[f'mimic_los_ge_T{T}']}\nVentilated by T: {flow[f'mimic_ventilated_by_T{T}']}\n"
               f"Alive at T = analysed: {flow[f'mimic_analysed_T{T}']}\nIn-hospital deaths: {flow[f'deaths_T{T}']}")
        ax.text(x, 0.40, txt, ha="center", va="center", bbox=dict(boxstyle="round", fc="#efe"), transform=ax.transAxes)
    fig.savefig(f"{out}/fig_cohort_flow.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", default="results")
    ap.add_argument("--boot", type=int, default=C.N_BOOT)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    np.random.seed(C.SEED)
    stays, flow = build_cohort(a.data)
    vit, lab = load_events(a.data, stays)
    sot = {"target_sentence": C.TARGET_SENTENCE, "cohort": flow,
           "bootstrap": {"n_resamples": a.boot, "unit": "patient", "ci": "percentile 95%"}}
    for T in C.HORIZONS:
        sot[f"metrics_T{T}"] = analyse_horizon(T, stays[T], vit, lab, a.out, a.boot)
    flow_figure(flow, a.out)
    sot["config"] = {"seed": C.SEED, "class_weights": C.USE_CLASS_WEIGHTS, "test_size": C.TEST_SIZE,
                     "dca_range": [C.DCA_THRESHOLDS[0], C.DCA_THRESHOLDS[-1]],
                     "probabilities": "natural prevalence scale" if not C.USE_CLASS_WEIGHTS else "recalibrated (Platt)"}
    path = f"{a.out}/source_of_truth.json"
    json.dump(sot, open(path, "w"), indent=2)
    log = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
           "scikit-learn": sklearn.__version__, "lightgbm": lightgbm.__version__, "mimic_version": C.MIMIC_VERSION,
           "vent_itemid": C.VENT_ITEMID, "seed": C.SEED, "data_dir": a.data, "runtime_s": round(time.time() - t0, 1),
           "source_of_truth_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
    json.dump(log, open(f"{a.out}/run_log.json", "w"), indent=2)
    print("done ->", path)


if __name__ == "__main__":
    main()
