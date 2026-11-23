"""LR (L2) and LightGBM. No class weighting by default; recalibration if weights are enabled."""
import numpy as np
import lightgbm as lgb
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from . import config as C
from .evaluation import logit


def split(X, seed=C.SEED):
    """Patient-level stratified split (one row per patient, so no patient appears in two parts)."""
    tr, te = train_test_split(np.arange(len(X)), test_size=C.TEST_SIZE, stratify=X.y, random_state=seed)
    tr, va = train_test_split(tr, test_size=C.VAL_SIZE, stratify=X.y.values[tr], random_state=seed)
    return tr, va, te


def _platt(p_val, y_val):
    m = LogisticRegression(C=1e12, max_iter=1000).fit(logit(p_val).reshape(-1, 1), y_val)
    return lambda p: m.predict_proba(logit(p).reshape(-1, 1))[:, 1]


def fit_predict(model_name, Xtr, ytr, Xva, yva, Xte, seed=C.SEED):
    """Returns (test probabilities, fitted model). Natural-prevalence probabilities."""
    cw = "balanced" if C.USE_CLASS_WEIGHTS else None
    if model_name == "LR":
        m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                          LogisticRegression(C=1.0, max_iter=2000, class_weight=cw, random_state=seed))
        m.fit(Xtr, ytr)
        pv, pt = m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]
    elif model_name == "LGBM":
        m = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.03, num_leaves=31, min_child_samples=50,
                               subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                               class_weight=cw, random_state=seed, deterministic=True, force_row_wise=True,
                               n_jobs=1, verbose=-1)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], callbacks=[lgb.early_stopping(100, verbose=False)])
        pv, pt = m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]
    else:
        raise ValueError(model_name)
    if C.USE_CLASS_WEIGHTS:           # restore natural-prevalence scale before Brier / calibration / DCA
        pt = _platt(pv, yva)(pt)
    return pt, m
