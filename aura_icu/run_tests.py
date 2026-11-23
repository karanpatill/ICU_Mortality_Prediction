"""Chapter 8 test table: python run_tests.py --out results/table_tests.csv
Every row records Input, Expected, Actual and Pass/Fail."""
import argparse, os, shutil, tempfile, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from aura import config as C
from aura.features import staleness_hours, assert_no_leakage, LeakageError, build_features
from aura import evaluation as E

rows = []
def record(tid, inp, exp, fn):
    try:
        actual, ok = fn()
    except Exception as e:                       # a crash is a fail, recorded honestly
        actual, ok = f"exception: {e!r}", False
    rows.append(dict(test_id=tid, input=inp, expected=exp, actual=actual, result="Pass" if ok else "Fail"))

def t01():
    v = staleness_hours(18.0, 24); return f"staleness = {v}", v == 6.0
def t02():
    v = staleness_hours(None, 24); return f"staleness = {v}", v == 48.0
def t02b():
    v = staleness_hours(float("nan"), 48); return f"staleness = {v}", v == 96.0
def t03():
    try:
        assert_no_leakage(np.array([1.0, 23.9, 24.5]), 24)
    except LeakageError as e:
        return f"LeakageError raised: {e}", True
    return "no error raised", False
def t03b():
    assert_no_leakage(np.array([0.0, 12.0, 24.0]), 24); return "no error (boundary t = T allowed)", True
def t04():
    rng = np.random.default_rng(1); p = rng.uniform(0.02, 0.98, 200_000); y = (rng.random(p.size) < p).astype(int)
    s, i = E.calibration_fit(y, p); return f"slope = {s:.3f}, intercept = {i:.3f}", abs(s - 1) < 0.03 and abs(i) < 0.03
def t05():
    rng = np.random.default_rng(2); p = rng.uniform(0.02, 0.98, 50_000); y = (rng.random(p.size) < 1 - p).astype(int)
    s, _ = E.calibration_fit(y, p); return f"slope = {s:.3f}", s < 0
def t06():
    idx = E.bootstrap_indices(500, 1000, 0); ok = idx.shape == (1000, 500) and idx.min() >= 0 and idx.max() < 500
    return f"shape = {idx.shape}, range = [{idx.min()}, {idx.max()}]", ok
def t07():
    th = [0.1, 0.2]; y = np.array([1, 0] * 50); nb = E.net_benefit(y, np.ones(100), th); ta = E.treat_all(y, th)
    return f"model(all-positive) NB = {np.round(nb, 4).tolist()}, treat-all NB = {np.round(ta, 4).tolist()}", np.allclose(nb, ta)

def t08():                                       # integration: synthetic cohort -> source_of_truth
    from aura import synthetic
    import subprocess, sys, json
    d = tempfile.mkdtemp(); synthetic.make(d + "/data", n=600, seed=3)
    r = subprocess.run([sys.executable, "-m", "aura.run_all", "--data", d + "/data", "--out", d + "/out", "--boot", "10"],
                       capture_output=True, text=True)
    sot = json.load(open(d + "/out/source_of_truth.json"))
    ok = r.returncode == 0 and "metrics_T24" in sot and "metrics_T48" in sot and os.path.exists(d + "/out/fig_dca_T24.png")
    shutil.rmtree(d, ignore_errors=True)
    return f"return code {r.returncode}; keys = {sorted(sot)[:4]}...", ok

def t09():                                       # leakage audit: features unchanged when post-T data are added
    from aura import synthetic
    from aura.cohort import build_cohort
    from aura.features import load_events
    d = tempfile.mkdtemp(); synthetic.make(d + "/data", n=400, seed=4)
    stays, _ = build_cohort(d + "/data"); vit, lab = load_events(d + "/data", stays)
    s = stays[24]; a = build_features(s, vit, lab, 24)
    late = lab.merge(s[["hadm_id", "intime"]], on="hadm_id").assign(charttime=lambda x: x.intime + pd.Timedelta(hours=30), valuenum=99.0)
    late = late[["hadm_id", "charttime", "name", "valuenum"]].drop_duplicates(["hadm_id", "name"])
    b = build_features(s, vit, pd.concat([lab, late], ignore_index=True), 24)
    same = a.drop(columns=[]).equals(b)
    shutil.rmtree(d, ignore_errors=True)
    return f"features identical after injecting {len(late)} post-T lab rows: {same}", same

record("T-01", "Lab last measured 6 h before T = 24 (t_last = 18 h)", "staleness = 6.0", t01)
record("T-02", "Lab never measured before T = 24", "staleness = 48.0 (sentinel 2*T)", t02)
record("T-02b", "Lab never measured, T = 48 (NaN input)", "staleness = 96.0 (sentinel 2*T)", t02b)
record("T-03", "Event at 24.5 h used for landmark T = 24", "LeakageError raised", t03)
record("T-03b", "Events at 0, 12, 24 h for T = 24", "No error (t <= T allowed)", t03b)
record("T-04", "Perfectly calibrated synthetic predictions (n = 200,000)", "slope ~ 1, intercept ~ 0 (tol 0.03)", t04)
record("T-05", "Anti-correlated synthetic predictions", "slope < 0", t05)
record("T-06", "Bootstrap index matrix, n = 500 patients, B = 1000", "shape (1000, 500), indices in [0, 499]", t06)
record("T-07", "DCA: predict-everyone-positive model", "Net benefit equals treat-all", t07)
record("T-08", "Full pipeline on synthetic cohort (n = 600)", "Runs; source_of_truth.json and figures produced", t08)
record("T-09", "Inject post-T lab values (t = 30 h) for T = 24", "Feature matrix unchanged", t09)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/table_tests.csv"); a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    df = pd.DataFrame(rows); df.to_csv(a.out, index=False)
    pd.set_option("display.max_colwidth", 80, "display.width", 200); print(df[["test_id", "result", "actual"]].to_string(index=False))
    raise SystemExit(0 if (df.result == "Pass").all() else 1)
