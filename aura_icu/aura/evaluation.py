"""Metrics, patient-level bootstrap, calibration, decision-curve analysis."""
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.linear_model import LogisticRegression

EPS = 1e-6


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def calibration_fit(y, p):
    """Logistic regression of outcome on the linear predictor logit(p): returns (slope, intercept)."""
    lr = LogisticRegression(C=1e12, solver="lbfgs", max_iter=1000)
    lr.fit(logit(p).reshape(-1, 1), y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def point_metrics(y, p):
    s, i = calibration_fit(y, p)
    return {"auroc": float(roc_auc_score(y, p)), "auprc": float(average_precision_score(y, p)),
            "brier": float(brier_score_loss(y, p)), "cal_slope": s, "cal_intercept": i}


def bootstrap_indices(n, B, seed):
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(B, n))   # rows = patients (one row per patient)


def boot_metrics(y, preds, idx):
    """preds: dict name->p. Returns dict name->dict metric->array(B). Same resamples for every model (paired)."""
    out = {k: {m: [] for m in ("auroc", "auprc", "brier", "cal_slope", "cal_intercept")} for k in preds}
    for ix in idx:
        yb = y[ix]
        if yb.min() == yb.max():
            continue
        for k, p in preds.items():
            pb = p[ix]
            s, i = calibration_fit(yb, pb)
            out[k]["auroc"].append(roc_auc_score(yb, pb))
            out[k]["auprc"].append(average_precision_score(yb, pb))
            out[k]["brier"].append(brier_score_loss(yb, pb))
            out[k]["cal_slope"].append(s)
            out[k]["cal_intercept"].append(i)
    return {k: {m: np.array(v) for m, v in d.items()} for k, d in out.items()}


def ci(arr):
    return [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))]


def delta_summary(point_a, point_b, boot_a, boot_b, metric):
    """A minus B, paired. Two-sided bootstrap p-value (floored at 1/(B+1))."""
    d = boot_a[metric] - boot_b[metric]
    B = len(d)
    p = 2 * min((np.sum(d <= 0) + 1) / (B + 1), (np.sum(d >= 0) + 1) / (B + 1))
    return {"delta": float(point_a[metric] - point_b[metric]), "ci": ci(d), "p": float(min(p, 1.0))}


def net_benefit(y, p, thresholds):
    n = len(y)
    out = []
    for t in thresholds:
        pred = p >= t
        tp, fp = np.sum(pred & (y == 1)), np.sum(pred & (y == 0))
        out.append(float(tp / n - fp / n * t / (1 - t)))
    return out


def treat_all(y, thresholds):
    prev = y.mean()
    return [float(prev - (1 - prev) * t / (1 - t)) for t in thresholds]
