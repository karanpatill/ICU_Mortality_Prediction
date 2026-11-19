# whatif_sim.py - Counterfactual Intervention Laboratory
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units

import streamlit as st
import numpy as np
import pandas as pd
from components.utils import (
    load_model, load_schema, classify_risk, whatif_predict,
    get_ward_patients, SENTINEL_HOURS
)

def render_whatif_sim():
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=10)

    st.markdown("### 🧪 Counterfactual Intervention Simulation Lab")
    st.caption("Adjust clinical parameters and lab redraw schedules to see how interventions alter predicted mortality risk.")

    bed_options = [
        f"{row['bed_id']} | Stay #{row['stay_id']} | Risk: {row['risk_pct']:.1f}% | {row['first_careunit'][:25]}"
        for _, row in ward_df.iterrows()
    ]
    default_idx = st.session_state.get("selected_bed_idx", 0)
    selected_opt = st.selectbox("Select Target Inpatient", bed_options, index=default_idx)
    sel_idx = bed_options.index(selected_opt)
    patient = ward_df.iloc[sel_idx]
    
    before_pct = float(patient["risk_pct"])

    col_sim_left, col_sim_right = st.columns(2)
    overrides = {}

    with col_sim_left:
        st.markdown("#### 🔬 Metabolic & Arterial Biomarkers")

        cur_lac = float(patient.get("lactate_val", 2.0))
        new_lac = st.slider("Arterial Lactate (mmol/L) [Ref: 0.5 - 2.0]", 0.5, 15.0, float(round(cur_lac, 1)), 0.1)
        if abs(new_lac - cur_lac) > 0.05:
            overrides["lactate_val"] = new_lac

        cur_pao2 = float(patient.get("pao2_val", 85.0))
        new_pao2 = st.slider("PaO2 Partial Pressure (mmHg) [Ref: 75 - 100]", 30.0, 200.0, float(round(cur_pao2, 0)), 1.0)
        if abs(new_pao2 - cur_pao2) > 0.5:
            overrides["pao2_val"] = new_pao2

        cur_cr = float(patient.get("creatinine_val", 1.0))
        new_cr = st.slider("Serum Creatinine (mg/dL) [Ref: 0.6 - 1.2]", 0.3, 12.0, float(round(cur_cr, 1)), 0.1)
        if abs(new_cr - cur_cr) > 0.05:
            overrides["creatinine_val"] = new_cr

    with col_sim_right:
        st.markdown("#### ⏱️ Targeted Observation Recency (Staleness)")

        cur_ls = float(patient.get("lactate_staleness", 24.0))
        new_ls = st.slider("Lactate Staleness (Hours) [Slide to 0 for fresh draw]", 0.0, 48.0, float(round(min(cur_ls, 48.0), 1)), 0.5)
        if abs(new_ls - cur_ls) > 0.1:
            overrides["lactate_staleness"] = new_ls

        cur_ps = float(patient.get("pao2_staleness", 12.0))
        new_ps = st.slider("Arterial Blood Gas Staleness (Hours)", 0.0, 48.0, float(round(min(cur_ps, 48.0), 1)), 0.5)
        if abs(new_ps - cur_ps) > 0.1:
            overrides["pao2_staleness"] = new_ps

        cur_cs = float(patient.get("creatinine_staleness", 12.0))
        new_cs = st.slider("Renal Panel Staleness (Hours)", 0.0, 48.0, float(round(min(cur_cs, 48.0), 1)), 0.5)
        if abs(new_cs - cur_cs) > 0.1:
            overrides["creatinine_staleness"] = new_cs

    st.divider()

    # Calculate Counterfactual Risk
    if overrides:
        after_pct = whatif_predict(patient, overrides, model, schema) * 100.0
    else:
        after_pct = before_pct

    delta = after_pct - before_pct

    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline Risk", f"{before_pct:.1f}%")
    c2.metric("Simulated Counterfactual Risk", f"{after_pct:.1f}%")
    c3.metric(
        "Risk Delta",
        f"{delta:+.1f}%",
        delta=f"{delta:+.1f}%",
        delta_color="inverse"
    )

    if delta < -3.0:
        st.success("✅ INTERVENTION IMPACT: Refreshing stale diagnostic markers significantly reduces clinical uncertainty and predicted risk.")
    elif delta > 3.0:
        st.error("⚠️ DETERIORATION WARNING: Simulated biomarker deterioration markedly elevates patient mortality risk.")
    else:
        st.info("ℹ️ Minimal change in predicted risk with current adjustments.")
