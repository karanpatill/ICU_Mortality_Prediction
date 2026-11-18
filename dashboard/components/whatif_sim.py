# whatif_sim.py - Clinical Intervention Simulation Laboratory
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from components.utils import (
    load_model, load_schema, classify_risk, whatif_predict,
    get_ward_patients, SENTINEL_HOURS
)

def render_whatif_sim():
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=12)

    st.markdown("""
    <div style="margin-bottom:14px;border-bottom:1px solid #1c2738;padding-bottom:8px;">
        <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:2px;text-transform:uppercase;">
            CLINICAL COUNTERFACTUAL SIMULATOR &bull; DECISION SUPPORT ENGINE
        </div>
        <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:#edf2f7;letter-spacing:1px;">
            COUNTERFACTUAL INTERVENTION EXPERIMENTATION
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Inpatient Selection
    bed_options = [
        f"{row['bed_id']} | Risk: {row['risk_pct']:.1f}% | Age: {int(row['age'])}y | {str(row['first_careunit'])[:28]}"
        for _, row in ward_df.iterrows()
    ]
    default_idx = st.session_state.get("selected_bed_idx", 0)
    selected_opt = st.selectbox("Select Target Inpatient", bed_options, index=default_idx, label_visibility="collapsed")
    sel_idx = int(selected_opt.split("|")[0].replace("BED-", "").strip()) - 1
    patient = ward_df.iloc[sel_idx]
    
    before_pct = float(patient["risk_pct"])
    before_cls = classify_risk(before_pct)

    col_sim_left, col_sim_right = st.columns([1.5, 1.5])
    overrides = {}

    with col_sim_left:
        st.markdown("""
        <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;">
            PHYSIOLOGICAL / METABOLIC BIOMARKERS
        </div>
        """, unsafe_allow_html=True)

        cur_lac = float(patient.get("lactate_val", 2.0))
        new_lac = st.slider("Arterial Lactate (mmol/L) [Ref: 0.5 – 2.0]", 0.5, 15.0, float(round(cur_lac, 1)), 0.1)
        if abs(new_lac - cur_lac) > 0.05:
            overrides["lactate_val"] = new_lac

        cur_pao2 = float(patient.get("pao2_val", 85.0))
        new_pao2 = st.slider("PaO2 Partial Pressure (mmHg) [Ref: 75 – 100]", 30.0, 200.0, float(round(cur_pao2, 0)), 1.0)
        if abs(new_pao2 - cur_pao2) > 0.5:
            overrides["pao2_val"] = new_pao2

        cur_cr = float(patient.get("creatinine_val", 1.0))
        new_cr = st.slider("Serum Creatinine (mg/dL) [Ref: 0.6 – 1.2]", 0.3, 12.0, float(round(cur_cr, 1)), 0.1)
        if abs(new_cr - cur_cr) > 0.05:
            overrides["creatinine_val"] = new_cr

    with col_sim_right:
        st.markdown("""
        <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;">
            MEASUREMENT STALENESS DECAY (HOURS SINCE DRAW)
        </div>
        """, unsafe_allow_html=True)

        cur_ls = float(patient.get("lactate_staleness", 24.0))
        new_ls = st.slider("Lactate Staleness (Hours) [Slide to 0 for Fresh Draw]", 0.0, 48.0, float(round(min(cur_ls, 48.0), 1)), 0.5)
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

    # Calculate Counterfactual Risk
    if overrides:
        after_pct = whatif_predict(patient, overrides, model, schema) * 100.0
    else:
        after_pct = before_pct

    after_cls = classify_risk(after_pct)
    delta = after_pct - before_pct

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Counterfactual Risk Comparison Cards
    c1, c2, c3 = st.columns([1, 1, 1.2])

    with c1:
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-top:3px solid {before_cls['color']};border-radius:4px;padding:12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">BASELINE RISK</div>
            <div style="font-family:var(--font-display);font-size:2.4rem;font-weight:700;color:{before_cls['color']};margin:4px 0;">
                {before_pct:.1f}%
            </div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:#718096;">{before_cls['label']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-top:3px solid {after_cls['color']};border-radius:4px;padding:12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">SIMULATED OUTCOME</div>
            <div style="font-family:var(--font-display);font-size:2.4rem;font-weight:700;color:{after_cls['color']};margin:4px 0;">
                {after_pct:.1f}%
            </div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:#718096;">{after_cls['label']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        delta_color = "#ff1744" if delta > 0 else ("#00e676" if delta < 0 else "#718096")
        delta_str = f"+{delta:.1f}%" if delta > 0 else f"{delta:.1f}%"
        action_recom = "STAT LAB REFRESH RECOMMENDED: High uncertainty reduction observed when staleness is resolved." if delta < -3 else ("STABILIZATION THERAPY INDICATED" if delta > 3 else "HOMEOSTASIS MAINTAINED")
        
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-radius:4px;padding:12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">UNCERTAINTY / RISK DELTA</div>
            <div style="font-family:var(--font-display);font-size:2.4rem;font-weight:700;color:{delta_color};margin:4px 0;">
                {delta_str}
            </div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:#edf2f7;">{action_recom}</div>
        </div>
        """, unsafe_allow_html=True)
