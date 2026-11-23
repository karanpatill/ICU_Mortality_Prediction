"""Cohort construction with an exact flow table. Works on MIMIC-IV CSV(.gz) files."""
import pandas as pd
from . import config as C


def _read(path, **kw):
    return pd.read_csv(path, **kw)


def build_cohort(data_dir, horizons=C.HORIZONS):
    """Returns (stays_df, flow_dict). One row per patient: the first ICU stay with invasive ventilation."""
    p = lambda *a: "/".join((data_dir,) + a)
    ext = ".csv.gz" if _exists(p("hosp", "patients.csv.gz")) else ".csv"
    patients = _read(p("hosp", "patients" + ext),
                     usecols=["subject_id", "gender", "anchor_age"])
    adm = _read(p("hosp", "admissions" + ext), parse_dates=["deathtime", "admittime", "dischtime"],
                usecols=["subject_id", "hadm_id", "admittime", "dischtime", "deathtime",
                         "hospital_expire_flag"])
    icu = _read(p("icu", "icustays" + ext), parse_dates=["intime", "outtime"],
                usecols=["subject_id", "hadm_id", "stay_id", "intime", "outtime"])
    proc = _read(p("icu", "procedureevents" + ext), parse_dates=["starttime", "endtime"],
                 usecols=["stay_id", "itemid", "starttime", "endtime"])

    flow = {"mimic_version": C.MIMIC_VERSION, "mimic_raw_icu_stays": int(len(icu)),
            "mimic_raw_patients_with_icu_stay": int(icu.subject_id.nunique())}

    df = icu.merge(patients, on="subject_id").merge(adm, on=["subject_id", "hadm_id"])
    df = df[df.anchor_age >= 18]
    flow["mimic_after_age"] = int(len(df))
    flow["mimic_after_age_patients"] = int(df.subject_id.nunique())

    vent = proc[proc.itemid == C.VENT_ITEMID].groupby("stay_id").starttime.min().rename("vent_start")
    df = df.merge(vent, on="stay_id", how="inner")
    df = df.sort_values(["subject_id", "intime"]).drop_duplicates("subject_id", keep="first")
    flow["mimic_ventilated"] = int(len(df))     # first ventilated ICU stay per patient

    df["los_h"] = (df.outtime - df.intime).dt.total_seconds() / 3600
    df["vent_start_h"] = (df.vent_start - df.intime).dt.total_seconds() / 3600
    df["death_h"] = (df.deathtime - df.intime).dt.total_seconds() / 3600
    df["y"] = df.hospital_expire_flag.astype(int)
    stays = {}
    for T in horizons:
        d = df[df.los_h >= T]
        n_los = len(d)
        d = d[d.vent_start_h <= T]               # ventilated by the landmark (no future info)
        n_vent = len(d)
        d = d[d.death_h.isna() | (d.death_h > T)]  # alive at T
        flow[f"mimic_los_ge_T{T}"] = int(n_los)
        flow[f"mimic_ventilated_by_T{T}"] = int(n_vent)
        flow[f"mimic_survived_T{T}"] = int(len(d))
        flow[f"mimic_analysed_T{T}"] = int(len(d))
        flow[f"deaths_T{T}"] = int(d.y.sum())
        flow[f"prevalence_T{T}"] = float(d.y.mean()) if len(d) else None
        d = d.copy()
        d["T"] = T
        stays[T] = d.reset_index(drop=True)
    return stays, flow


def _exists(path):
    import os
    return os.path.exists(path)
