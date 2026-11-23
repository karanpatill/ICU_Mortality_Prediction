"""Synthetic MIMIC-IV-shaped tables. ONLY for testing the pipeline. Never report these numbers."""
import os
import numpy as np
import pandas as pd
from . import config as C


def make(out_dir, n=3000, seed=0):
    rng = np.random.default_rng(seed)
    os.makedirs(f"{out_dir}/hosp", exist_ok=True)
    os.makedirs(f"{out_dir}/icu", exist_ok=True)
    t0 = pd.Timestamp("2150-01-01")
    sid = np.arange(1, n + 1)
    age = rng.integers(16, 95, n)
    sev = rng.normal(0, 1, n)                                   # latent severity
    p_die = 1 / (1 + np.exp(-(-1.6 + 0.9 * sev + 0.02 * (age - 60))))
    died = rng.random(n) < p_die
    los = np.where(died, rng.gamma(2.0, 40, n), rng.gamma(2.5, 45, n)) + 4
    intime = t0 + pd.to_timedelta(rng.integers(0, 10000, n), unit="h")
    outtime = intime + pd.to_timedelta(los, unit="h")
    death = outtime.where(died)
    pd.DataFrame({"subject_id": sid, "gender": rng.choice(["M", "F"], n), "anchor_age": age}
                 ).to_csv(f"{out_dir}/hosp/patients.csv", index=False)
    pd.DataFrame({"subject_id": sid, "hadm_id": sid + 1000, "admittime": intime - pd.Timedelta(hours=2),
                  "dischtime": outtime, "deathtime": death, "hospital_expire_flag": died.astype(int)}
                 ).to_csv(f"{out_dir}/hosp/admissions.csv", index=False)
    pd.DataFrame({"subject_id": sid, "hadm_id": sid + 1000, "stay_id": sid + 5000,
                  "intime": intime, "outtime": outtime}).to_csv(f"{out_dir}/icu/icustays.csv", index=False)
    vent = rng.random(n) < 0.7
    vs = intime + pd.to_timedelta(rng.uniform(0, 30, n), unit="h")
    pd.DataFrame({"stay_id": (sid + 5000)[vent], "itemid": C.VENT_ITEMID, "starttime": vs[vent],
                  "endtime": vs[vent] + pd.Timedelta(hours=40)}).to_csv(f"{out_dir}/icu/procedureevents.csv", index=False)

    rows = []
    base = {220045: 85, 220179: 120, 220180: 65, 220181: 80, 220210: 18, 220277: 96, 223762: 37.0}
    for i in range(n):
        for h in np.arange(0.5, min(los[i], 72), 3.0):
            for it, b in base.items():
                v = b + sev[i] * {220045: 8, 220179: -10, 220180: -5, 220181: -6, 220210: 3, 220277: -1.5, 223762: 0.3}[it] \
                    + rng.normal(0, b * 0.05)
                rows.append((sid[i] + 5000, intime[i] + pd.Timedelta(hours=h), it, v))
    pd.DataFrame(rows, columns=["stay_id", "charttime", "itemid", "valuenum"]).to_csv(f"{out_dir}/icu/chartevents.csv", index=False)

    lab_base = {50813: 2.0, 50912: 1.2, 51006: 25, 51301: 11, 51222: 11, 51265: 220, 50983: 139,
                50971: 4.2, 50882: 23, 50931: 130, 50885: 1.0, 50820: 7.38, 50902: 104}
    lab_eff = {50813: 1.2, 50912: 0.5, 51006: 8, 51301: 3, 51222: -1, 51265: -40, 50983: -1,
               50971: 0.1, 50882: -2, 50931: 15, 50885: 0.8, 50820: -0.04, 50902: 0}
    rows = []
    for i in range(n):
        rate = 1 / (14 - 3 * np.clip(sev[i], -1, 2))           # sicker -> more frequent sampling
        for it, b in lab_base.items():
            if rng.random() < 0.1:
                continue                                         # never measured
            t = rng.exponential(1 / rate)
            while t < min(los[i], 80):
                rows.append((sid[i] + 1000, intime[i] + pd.Timedelta(hours=t), it,
                             b + sev[i] * lab_eff[it] + rng.normal(0, abs(b) * 0.08)))
                t += rng.exponential(1 / rate)
    pd.DataFrame(rows, columns=["hadm_id", "charttime", "itemid", "valuenum"]).to_csv(f"{out_dir}/hosp/labevents.csv", index=False)
