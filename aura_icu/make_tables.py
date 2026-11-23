"""Turns results/source_of_truth.json into report tables. Nothing is typed by hand.
   python make_tables.py --results results"""
import argparse, json
import pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--results", default="results"); a = ap.parse_args()
s = json.load(open(f"{a.results}/source_of_truth.json"))
f3 = lambda x: f"{x:.3f}"
ci = lambda v: f"({v[0]:.3f}-{v[1]:.3f})"
pv = lambda p: "<0.001" if p < 0.001 else f"{p:.3f}"

rows = []
for T in (24, 48):
    m = s[f"metrics_T{T}"]
    for model in ("LR", "LGBM"):
        r = m["primary"][model]
        rows.append({"T (h)": T, "Model": {"LR": "Logistic regression (L2)", "LGBM": "LightGBM"}[model],
                     "N test": m["n_test"], "Deaths": m["deaths_test"],
                     "AUROC (95% CI)": f"{f3(r['auroc'])} {ci(r['auroc_ci'])}",
                     "AUPRC (95% CI)": f"{f3(r['auprc'])} {ci(r['auprc_ci'])}",
                     "Brier": f"{f3(r['brier'])} {ci(r['brier_ci'])}",
                     "Cal. slope (95% CI)": f"{r['cal_slope']:.2f} ({r['cal_slope_ci'][0]:.2f}-{r['cal_slope_ci'][1]:.2f})",
                     "Cal. intercept (95% CI)": f"{r['cal_intercept']:.2f} ({r['cal_intercept_ci'][0]:.2f}-{r['cal_intercept_ci'][1]:.2f})"})
pd.DataFrame(rows).to_csv(f"{a.results}/table_metrics.csv", index=False)

rows = []
for T in (24, 48):
    for model, d in s[f"metrics_T{T}"]["delta_tls_minus_base"].items():
        for met in ("auroc", "auprc"):
            x = d[met]
            rows.append({"T (h)": T, "Model": model, "Metric": met.upper(),
                         "Absolute difference (TLS minus no staleness)": f"{x['delta']:+.4f}",
                         "95% CI": f"({x['ci'][0]:+.4f} to {x['ci'][1]:+.4f})", "Bootstrap p": pv(x["p"])})
pd.DataFrame(rows).to_csv(f"{a.results}/table_delta.csv", index=False)

rows = []
for T in (24, 48):
    for model, d in s[f"metrics_T{T}"]["ablation"].items():
        for fs, v in d.items():
            rows.append({"T (h)": T, "Model": model, "Feature set": {"base": "No staleness", "tls": "Staleness + sentinel (TLS)",
                         "miss": "Missing indicator only", "both": "Staleness + missing indicator"}[fs],
                         "AUROC": f3(v["auroc"]), "AUPRC": f3(v["auprc"])})
pd.DataFrame(rows).to_csv(f"{a.results}/table_ablation.csv", index=False)

pd.DataFrame([{"Step": k, "Count": v} for k, v in s["cohort"].items()]).to_csv(f"{a.results}/table_flow.csv", index=False)
print("tables written to", a.results)
