"""Event loading and landmark feature engineering with a hard leakage guard."""
import numpy as np
import pandas as pd
from . import config as C

CHUNK = 5_000_000


class LeakageError(AssertionError):
    pass


def staleness_hours(t_last_h, T):
    """Hours between the last measurement and the landmark T.
    Never measured (t_last_h is None/NaN) -> sentinel 2*T."""
    if t_last_h is None or (isinstance(t_last_h, float) and np.isnan(t_last_h)):
        return 2.0 * T
    return float(T - t_last_h)


def assert_no_leakage(hours_since_intime, T):
    """Every event used to build features must satisfy t <= T."""
    if len(hours_since_intime) and float(np.max(hours_since_intime)) > T + 1e-9:
        raise LeakageError(f"event at {np.max(hours_since_intime):.2f} h used for landmark T={T} h")


def _find(data_dir, *parts):
    import os
    base = "/".join((data_dir,) + parts)
    return base + ".csv.gz" if os.path.exists(base + ".csv.gz") else base + ".csv"


def load_events(data_dir, stays_by_T):
    """Stream chartevents/labevents once, keeping only cohort rows and needed itemids."""
    all_stays = pd.concat(stays_by_T.values()).drop_duplicates("stay_id")
    stay_ids, hadm_ids = set(all_stays.stay_id), set(all_stays.hadm_id)
    v_parts, l_parts = [], []
    for ch in pd.read_csv(_find(data_dir, "icu", "chartevents"), chunksize=CHUNK, parse_dates=["charttime"],
                          usecols=["stay_id", "charttime", "itemid", "valuenum"]):
        ch = ch[ch.itemid.isin(C.VITALS) & ch.stay_id.isin(stay_ids)]
        v_parts.append(ch)
    for ch in pd.read_csv(_find(data_dir, "hosp", "labevents"), chunksize=CHUNK, parse_dates=["charttime"],
                          usecols=["hadm_id", "charttime", "itemid", "valuenum"]):
        ch = ch[ch.itemid.isin(C.LABS) & ch.hadm_id.isin(hadm_ids)]
        l_parts.append(ch)
    vit = pd.concat(v_parts, ignore_index=True)
    lab = pd.concat(l_parts, ignore_index=True)
    vit["name"] = vit.itemid.map(C.VITALS)
    lab["name"] = lab.itemid.map(C.LABS)
    f = vit.name == "temp_f"
    vit.loc[f, "valuenum"] = (vit.loc[f, "valuenum"] - 32) * 5 / 9
    vit.loc[f, "name"] = "temp_c"
    return vit[["stay_id", "charttime", "name", "valuenum"]], lab[["hadm_id", "charttime", "name", "valuenum"]]


def _clean(ev):
    ev = ev.dropna(subset=["valuenum"]).copy()
    ok = pd.Series(True, index=ev.index)
    for name, (lo, hi) in C.RANGES.items():
        m = ev.name == name
        ok[m] = ev.loc[m, "valuenum"].between(lo, hi)
    return ev[ok]


def _window(ev, stays, key, T):
    """Attach hours-since-ICU-admission; keep events in [0, T]; run the leakage guard."""
    ev = ev.merge(stays[list(dict.fromkeys([key, "stay_id", "intime"]))], on=key)
    ev["h"] = (ev.charttime - ev.intime).dt.total_seconds() / 3600
    ev = ev[(ev.h >= 0) & (ev.h <= T)]
    assert_no_leakage(ev.h.values, T)
    return ev


def build_features(stays, vit, lab, T):
    """One row per patient. Columns: y, static, vital summaries, lab last values,
    lab staleness (sentinel 2*T), lab missing flags."""
    stays = stays.copy()
    X = stays[["subject_id", "stay_id", "y"]].copy()
    X["age"] = stays.anchor_age.values
    X["male"] = (stays.gender.values == "M").astype(int)
    X = X.set_index("stay_id")

    v = _window(_clean(vit), stays, "stay_id", T)
    v = v.sort_values(["stay_id", "name", "h"])
    g = v.groupby(["stay_id", "name"]).valuenum
    agg = pd.concat({"last": g.last(), "mean": g.mean(), "min": g.min(), "max": g.max()}, axis=1).unstack("name")
    agg.columns = [f"{n}_{s}" for s, n in agg.columns]
    X = X.join(agg)

    l = _window(_clean(lab), stays, "hadm_id", T)
    l = l.sort_values(["stay_id", "name", "h"])
    g = l.groupby(["stay_id", "name"])
    last = pd.concat({"last": g.valuenum.last(), "t_last": g.h.last()}, axis=1)
    lv = last["last"].unstack("name")
    lt = last["t_last"].unstack("name")
    for name in C.LAB_NAMES:
        X[f"{name}_last"] = lv[name] if name in lv else np.nan
        t_last = lt[name].reindex(X.index) if name in lt else pd.Series(np.nan, index=X.index)
        X[f"{name}_staleness"] = [staleness_hours(t, T) for t in t_last]
        X[f"{name}_missing"] = t_last.isna().astype(int).values
    for name in C.VITAL_NAMES:
        for s in ("last", "mean", "min", "max"):
            col = f"{name}_{s}"
            if col not in X:
                X[col] = np.nan
    return X.reset_index()


def feature_sets(X):
    static = ["age", "male"]
    vit = [f"{n}_{s}" for n in C.VITAL_NAMES for s in ("last", "mean", "min", "max")]
    last = [f"{n}_last" for n in C.LAB_NAMES]
    stale = [f"{n}_staleness" for n in C.LAB_NAMES]
    miss = [f"{n}_missing" for n in C.LAB_NAMES]
    base = static + vit + last
    return {"base": base, "tls": base + stale, "miss": base + miss, "both": base + stale + miss}
