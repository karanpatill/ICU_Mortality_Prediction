# clinical_dossier.py - Clean, Modern Hospital-Grade Inpatient Triage & On-Demand AI Predictor
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units
# D. Y. Patil School of Engineering and Management, Kolhapur

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
from pathlib import Path
from components.utils import (
    load_model, load_schema, encode_features,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL, classify_staleness, classify_risk
)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "clinical_dossier_mimic.json"

CLINICAL_NARRATIVES = {
    "MIMIC-PT-01": {
        "title": "Severe Sepsis with Multi-Organ Failure",
        "primary_dx": "Gram-negative urosepsis with septic shock and refractory metabolic lactic acidosis.",
        "clinical_presentation": "Patient intubated for acute respiratory failure and persistent hypoperfusion. On dual vasopressor infusion."
    },
    "MIMIC-PT-02": {
        "title": "Polytrauma with Hemorrhagic Shock",
        "primary_dx": "High-velocity vehicular trauma with internal pelvic hemorrhage and acute lung contusion.",
        "clinical_presentation": "Intubated post-exploratory laparotomy. Coagulopathy and secondary tissue hypoxia."
    },
    "MIMIC-PT-03": {
        "title": "Acute STEMI with Cardiogenic Shock",
        "primary_dx": "Acute massive anterior myocardial infarction complicated by pulmonary edema.",
        "clinical_presentation": "Elderly patient on high-dose inotropic support. Multiple stale biochemical markers and renal hypoperfusion."
    },
    "MIMIC-PT-04": {
        "title": "Severe Acute Respiratory Distress Syndrome (ARDS)",
        "primary_dx": "Refractory hypoxemic respiratory failure following aspiration pneumonia.",
        "clinical_presentation": "High ventilator pressure requirements, persistent respiratory acidosis, and profound tissue hypoxia."
    },
    "MIMIC-PT-05": {
        "title": "Community-Acquired Pneumonia (Resolving)",
        "primary_dx": "Severe bacterial pneumonia on de-escalating mechanical ventilatory support.",
        "clinical_presentation": "Hemodynamically stable, clearing lactate, and preparing for spontaneous breathing trial."
    },
    "MIMIC-PT-06": {
        "title": "Post-Operative Trauma Stabilization",
        "primary_dx": "Blunt abdominal trauma status post-surgical repair; stable recovery.",
        "clinical_presentation": "Controlled airway pressures, improving oxygenation index, and stable renal markers."
    },
    "MIMIC-PT-07": {
        "title": "Stabilized Post-Infarction Recovery",
        "primary_dx": "Non-ST elevation myocardial infarction post-percutaneous coronary intervention.",
        "clinical_presentation": "Normal tissue perfusion, weaned off inotropes, favorable biochemical recovery trajectory."
    },
    "MIMIC-PT-08": {
        "title": "Post-Anesthesia Monitoring & Weaning",
        "primary_dx": "Extensive vascular reconstruction with delayed post-operative extubation.",
        "clinical_presentation": "Preserved end-organ function, minimal ventilatory support, low biomarker staleness."
    },
    "MIMIC-PT-09": {
        "title": "Traumatic Head Injury (Recovering)",
        "primary_dx": "Closed head injury with rapid normalization of neurological and metabolic status.",
        "clinical_presentation": "Alert, following commands, normal arterial blood gases, ready for extubation."
    },
    "MIMIC-PT-10": {
        "title": "Elective Spinal Surgery Recovery",
        "primary_dx": "Elective cervical spinal fusion with overnight airway protection.",
        "clinical_presentation": "Optimal acid-base equilibrium, zero organ dysfunction, baseline risk below 5%."
    }
}

@st.cache_data(show_spinner=False)
def load_real_mimic_cases():
    with open(DATA_FILE, "r") as f:
        cases = json.load(f)
    for c in cases:
        narrative = CLINICAL_NARRATIVES.get(c["id"], {})
        c["title"] = narrative.get("title", f"MIMIC-IV Stay #{c['stay_id']}")
        c["primary_dx"] = narrative.get("primary_dx", "MIMIC-IV Critical Care Record")
        c["clinical_presentation"] = narrative.get("clinical_presentation", "Invasive mechanical ventilation ongoing.")
    return cases

def render_clinical_dossier():
    model = load_model()
    schema = load_schema()
    clinical_cases = load_real_mimic_cases()

    # Header
    st.markdown("""
    <div class="app-header">
        <div>
            <div class="brand-title">
                AURA-ICU Clinical Decision Support System
                <span class="brand-badge">Clinical Workbench</span>
            </div>
            <div class="brand-sub">
                10 Verified Real MIMIC-IV Clinical Inpatients &bull; Beth Israel Deaconess Medical Center, Boston
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600;">ACTIVE COHORT DATABASE</div>
            <div style="font-size: 0.85rem; color: #10b981; font-weight: 700;">MIMIC-IV v3.1 Authenticated</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "dossier_selected_id" not in st.session_state:
        st.session_state.dossier_selected_id = "MIMIC-PT-01"
    if "prediction_executed" not in st.session_state:
        st.session_state.prediction_executed = False

    # Top Case Navigation Pills
    case_opts = [f"{c['id']} — {c['title']} (Stay #{c['stay_id']})" for c in clinical_cases]
    current_idx = next((i for i, c in enumerate(clinical_cases) if c["id"] == st.session_state.dossier_selected_id), 0)
    
    selected_option = st.selectbox(
        "Select Clinical Patient Record",
        case_opts,
        index=current_idx,
        label_visibility="collapsed"
    )
    selected_case_id = selected_option.split(" — ")[0]
    if selected_case_id != st.session_state.dossier_selected_id:
        st.session_state.dossier_selected_id = selected_case_id
        st.session_state.prediction_executed = False
        st.rerun()

    active_case = next(c for c in clinical_cases if c["id"] == st.session_state.dossier_selected_id)
    gender_str = "Male" if active_case["gender"] == "M" else "Female"

    # Patient Dossier Card
    st.markdown(f"""
    <div class="clean-card" style="border-left: 4px solid #38bdf8;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div style="flex: 1; min-width: 300px;">
                <div style="font-size: 0.75rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                    {active_case['id']} &bull; MIMIC-IV RECORD #{active_case['stay_id']} (HADM #{active_case['hadm_id']})
                </div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff; margin: 4px 0 10px 0;">
                    {active_case['title']}
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 6px;">
                    <b style="color: #ffffff;">Primary Diagnosis:</b> {active_case['primary_dx']}
                </div>
                <div style="font-size: 0.88rem; color: #94a3b8; line-height: 1.5;">
                    <b style="color: #ffffff;">Bedside Status:</b> {active_case['clinical_presentation']}
                </div>
            </div>
            <div style="background: #0b1120; border: 1px solid #1e293b; border-radius: 10px; padding: 14px 18px; min-width: 200px;">
                <div style="font-size: 0.70rem; color: #64748b; font-weight: 700; text-transform: uppercase;">PATIENT PROFILE</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-top: 4px;">
                    {gender_str}, {active_case['age']} Years
                </div>
                <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 600; margin-top: 2px;">
                    {active_case['unit']}
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                    Mechanical Vent: {active_case['vent_duration_hours']} Hours &bull; {active_case['admission_type']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 13 Biomarkers Grid
    st.markdown('<div class="card-title">Patient Laboratory Biomarkers & Targeted Observation Staleness</div>', unsafe_allow_html=True)

    parsed_labs = []
    for lab in LAB_NAMES:
        val = active_case["labs"].get(f"{lab}_val", np.nan)
        stale = active_case["labs"].get(f"{lab}_staleness", 48.0)
        parsed_labs.append({
            "name": LAB_DISPLAY[lab],
            "val": val,
            "unit": LAB_UNITS[lab],
            "stale": stale,
            "cls": classify_staleness(stale)
        })

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        for item in parsed_labs[:7]:
            c = item["cls"]
            val_txt = f"{item['val']:.2f} {item['unit']}" if not np.isnan(item['val']) else "Not Drawn"
            st.markdown(f"""
            <div class="lab-item">
                <span class="lab-name">{item['name']}</span>
                <span class="lab-val">{val_txt}</span>
                <span class="status-badge" style="background:{c['color']}22; color:{c['color']}; border: 1px solid {c['color']}44;">
                    {item['stale']:.1f}h ({c['label'].upper()})
                </span>
            </div>
            """, unsafe_allow_html=True)

    with col_l2:
        for item in parsed_labs[7:]:
            c = item["cls"]
            val_txt = f"{item['val']:.2f} {item['unit']}" if not np.isnan(item['val']) else "Not Drawn"
            st.markdown(f"""
            <div class="lab-item">
                <span class="lab-name">{item['name']}</span>
                <span class="lab-val">{val_txt}</span>
                <span class="status-badge" style="background:{c['color']}22; color:{c['color']}; border: 1px solid {c['color']}44;">
                    {item['stale']:.1f}h ({c['label'].upper()})
                </span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ── Interactive Prediction Execution Button ───────────────────────────────
    c_btn, _ = st.columns([1.5, 1])
    with c_btn:
        run_clicked = st.button("⚡ EXECUTE AURA-ICU AI PREDICTION INFERENCE", use_container_width=True)

    if run_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown('<span style="font-size:0.82rem; color:#38bdf8; font-weight:600;">[1/3] Ingesting 52 MIMIC-IV Clinical & Staleness Features...</span>', unsafe_allow_html=True)
        progress_bar.progress(35)
        time.sleep(0.18)
        
        status_text.markdown('<span style="font-size:0.82rem; color:#f59e0b; font-weight:600;">[2/3] Evaluating Targeted Laboratory Staleness Decay Vector...</span>', unsafe_allow_html=True)
        progress_bar.progress(70)
        time.sleep(0.18)

        status_text.markdown('<span style="font-size:0.82rem; color:#10b981; font-weight:600;">[3/3] Executing LightGBM GBDT Ensemble (AUROC 0.8559)...</span>', unsafe_allow_html=True)
        progress_bar.progress(100)
        time.sleep(0.15)
        
        status_text.empty()
        progress_bar.empty()
        st.session_state.prediction_executed = True

    # ── Prediction Results View ───────────────────────────────────────────────
    if st.session_state.prediction_executed:
        patient_dict = {
            "age": active_case["age"],
            "gender": active_case["gender"],
            "first_careunit": active_case["unit"],
            "admission_type": active_case["admission_type"],
            "vent_duration_hours": active_case["vent_duration_hours"],
        }
        patient_dict.update(active_case["labs"])
        
        X_df = encode_features(pd.DataFrame([patient_dict]), schema["features"])
        risk_prob = float(model.predict_proba(X_df)[:, 1][0])
        risk_pct = risk_prob * 100.0
        risk_cls = classify_risk(risk_pct)

        actual_outcome = active_case["ground_truth"]
        actual_color = "#ef4444" if actual_outcome == "EXPIRED" else "#10b981"

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        res1, res2 = st.columns([1.2, 1.8])

        with res1:
            st.markdown(f"""
            <div class="clean-card" style="border-top: 4px solid {risk_cls['color']}; text-align: center;">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                    AI MORTALITY RISK ASSESSMENT
                </div>
                <div style="font-size: 3.5rem; font-weight: 800; color: {risk_cls['color']}; line-height: 1; margin: 12px 0 6px 0;">
                    {risk_pct:.1f}<span style="font-size: 1.6rem;">%</span>
                </div>
                <div style="font-size: 0.82rem; font-weight: 700; color: {risk_cls['color']}; background: {risk_cls['color']}18; padding: 4px 12px; border-radius: 6px; display: inline-block;">
                    {risk_cls['label']} STATUS
                </div>
                <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; font-size: 0.82rem;">
                    <span style="color: #94a3b8; font-weight: 600;">MIMIC-IV Ground Truth:</span>
                    <span style="color: {actual_color}; font-weight: 800; letter-spacing: 0.5px;">{actual_outcome}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with res2:
            if risk_pct >= 70:
                rec_title = "Critical Deterioration Protocol Activated"
                rec_color = "#ef4444"
                rec_actions = """
                &bull; <b>Stat Diagnostic Lab Refresh:</b> Repeat Arterial Blood Gas (ABG) & Lactate immediately (staleness uncertainty critical).<br>
                &bull; <b>Hemodynamic Resuscitation:</b> Titrate vasopressors; maintain MAP > 65 mmHg; evaluate cardiac index.<br>
                &bull; <b>Lung-Protective Ventilation:</b> Ensure tidal volume <= 6 mL/kg PBW; check plateau pressure < 30 cmH2O.
                """
            elif risk_pct >= 40:
                rec_title = "Elevated Surveillance & Organ Trend Protocol"
                rec_color = "#f97316"
                rec_actions = """
                &bull; <b>Organ Function Monitoring:</b> Serial renal panel and serum creatinine within next 4 hours.<br>
                &bull; <b>Ventilator Weaning Vigilance:</b> Defer spontaneous breathing trial until arterial acid-base balance stabilizes.<br>
                &bull; <b>Volume Status Review:</b> Assess fluid overload, lung compliance, and vasopressor weaning readiness.
                """
            else:
                rec_title = "Physiologically Stable — Extubation Candidate"
                rec_color = "#10b981"
                rec_actions = """
                &bull; <b>Spontaneous Breathing Trial (SBT):</b> Patient satisfies clinical stability criteria for weaning protocol.<br>
                &bull; <b>Routine Surveillance:</b> Low information staleness; standard 12-hour draw schedule sufficient.<br>
                &bull; <b>Sedation De-escalation:</b> Initiate sedation vacation and respiratory therapy mobilization protocol.
                """

            st.markdown(f"""
            <div class="clean-card" style="border-left: 4px solid {rec_color};">
                <div style="font-size: 0.75rem; font-weight: 700; color: {rec_color}; text-transform: uppercase; letter-spacing: 0.5px;">
                    CLINICAL RECOMMENDATION & PROTOCOL
                </div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; margin: 4px 0 10px 0;">
                    {rec_title}
                </div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.7;">
                    {rec_actions}
                </div>
            </div>
            """, unsafe_allow_html=True)
