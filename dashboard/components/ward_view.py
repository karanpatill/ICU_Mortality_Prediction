# ward_view.py - Central Nursing Station (10-Bed Inpatient Telemetry Overview)
# AURA-ICU: Clinical Decision Support System

import streamlit as st
import pandas as pd
from components.utils import (
    get_ward_patients, classify_risk, LAB_NAMES, classify_staleness
)

def render_ward_view():
    st.markdown("### 🏥 Central Nursing Station — 10-Bed Inpatient Surveillance")
    st.caption("Real-time clinical telemetry and targeted staleness overview across active ICU beds.")

    ward_df = get_ward_patients(n_beds=10)

    # Clean Top Metrics Bar
    total = len(ward_df)
    n_critical = (ward_df["risk_pct"] >= 70).sum()
    n_elevated = ((ward_df["risk_pct"] >= 50) & (ward_df["risk_pct"] < 70)).sum()
    n_watch    = ((ward_df["risk_pct"] >= 25) & (ward_df["risk_pct"] < 50)).sum()
    n_stable   = (ward_df["risk_pct"] < 25).sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Occupancy", f"{total} / 10 Beds")
    m2.metric("Critical (>70%)", str(n_critical))
    m3.metric("Elevated (50-70%)", str(n_elevated))
    m4.metric("Watch (25-50%)", str(n_watch))
    m5.metric("Stable (<25%)", str(n_stable))

    st.divider()

    # Clean Inpatients Table
    display_rows = []
    for _, row in ward_df.iterrows():
        display_rows.append({
            "Bed ID": row["bed_id"],
            "MIMIC Stay": f"#{row['stay_id']}",
            "Age / Gender": f"{row['age']}y / {row['gender']}",
            "Care Unit": row["first_careunit"],
            "Vent Duration": f"{int(row['vent_duration_hours'])} Hours",
            "AI Mortality Risk": f"{row['risk_pct']:.1f}%",
            "Clinical Status": classify_risk(row["risk_pct"])["label"],
            "Ground Truth": "EXPIRED" if row["outcome_death"] == 1 else "SURVIVED"
        })

    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
