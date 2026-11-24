# documentation.py - Project Documentation & Academic Report
# AURA-ICU: Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients
# Final Year B.E. Capstone Project (23CSEU7J12) - Academic Year 2026-27
# D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur

import streamlit as st
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def render_documentation():
    """Render comprehensive project documentation, clinical methodology, and experimental results."""

    st.markdown("""
    <div style="margin-bottom:18px;">
        <span class="section-header">PROJECT DOCUMENTATION & CLINICAL REPORT</span>
        <div style="font-size: 0.9rem; color: #64748b; margin-top: 4px;">
            Course Project (23CSEU7J12) | Department of Computer Science & Engineering | Academic Year 2026-27
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Executive Summary",
        "Clinical Methodology & Cohort",
        "Benchmark Results & Statistics",
        "Risk Analysis & Governance",
        "Project Team & Academic Record",
        "CDSS User Manual"
    ])

    # ─── TAB 1: EXECUTIVE SUMMARY ─────────────────────────────────────────────
    with tab1:
        st.markdown("""
        ### Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness
        
        **AURA-ICU** is a clinical decision support research prototype developed as a Final Year B.E. Capstone Project (Course Code: `23CSEU7J12`) 
        at **D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur**.
        
        ---
        
        #### 1. Clinical Background & Motivation
        Invasive mechanical ventilation is one of the most critical life-supporting interventions in intensive care units (ICUs). 
        Clinicians face a continuous dilemma: prolonged mechanical ventilation increases the risk of severe complications such as 
        ventilator-associated pneumonia (VAP) and barotrauma, whereas premature extubation carries the hazard of sudden respiratory 
        failure, re-intubation, and worsened in-hospital mortality. Continuous and dynamic risk assessment is required to support weaning and escalation decisions.
        
        #### 2. Limits of Conventional Static Severity Scores
        Traditional ICU severity scores such as **APACHE II** and **SOFA** compress a patient's clinical state into a single static number, 
        typically derived from the worst physiological measurements in the initial 24 hours of admission. Structurally, these scores:
        - Do not account for the longitudinal dynamic evolution of organ function.
        - Treat all measurements equally, regardless of when they were taken.
        - Are intended for population benchmarking rather than running bedside decision support.
        
        #### 3. The Measurement-Age Problem & "Silent Drift"
        In modern critical care telemetry, vital signs (heart rate, invasive blood pressures, SpO2) are logged continuously or every few minutes. 
        In contrast, laboratory blood draws (lactate, arterial blood gases, bilirubin, creatinine) occur at irregular intervals—often separated by 12, 24, or 48 hours.
        
        Standard machine learning models evaluate snapshots of the latest recorded values. Consequently, a creatinine measurement drawn 22 hours earlier 
        is treated as if it were drawn 5 minutes ago. We characterize this discrepancy as **silent drift**: the model receives an apparently current physiological input, 
        yet the underlying clinical reality may have significantly deteriorated.
        
        #### 4. The Core Innovation: Targeted Laboratory Staleness (TLS)
        Rather than relying on uncalibrated forward-filling or indiscriminate data dropping, AURA-ICU explicitly parameterizes the age of each laboratory test:
        - **Explicit Staleness Feature ($s_j$):** Time elapsed in hours between the most recent measurement and the landmark prediction horizon $T$:
          $$s_j = T - t_{\\text{last}, j}$$
        - **Conservative Sentinel Imputation ($2 \\times T$):** If a biomarker was never measured prior to landmark $T$, its staleness is deterministically assigned to $2T$ (e.g., $48\\text{ h}$ at $T=24\\text{ h}$ and $96\\text{ h}$ at $T=48\\text{ h}$), representing maximum uncertainty.
        - **Vital-Sign Preservation:** High-frequency vital signs are preserved in their native continuous form without artificial decay.
        - **Strict Landmark Design:** Prediction targets in-hospital mortality strictly among patients who survived to landmark $T$, preventing immortal-time bias in full compliance with the **TRIPOD+AI** statement.
        """)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Primary Dataset", "MIMIC-IV v3.1", "PhysioNet Credentialed")
        with col2:
            st.metric("T=24h Cohort", "23,427 Patients", "14.24% Mortality")
        with col3:
            st.metric("T=48h Cohort", "17,072 Patients", "17.07% Mortality")
        with col4:
            st.metric("Primary Models", "LightGBM + LR", "Paired Bootstrap B=1000")

    # ─── TAB 2: CLINICAL METHODOLOGY & COHORT ─────────────────────────────────
    with tab2:
        st.markdown("""
        ### Clinical Cohort Derivation & Feature Engineering
        
        #### 1. Landmark Cohort Selection Criteria
        From the Beth Israel Deaconess Medical Center **MIMIC-IV v3.1** database, adult ICU stays were filtered using a rigorous protocol:
        - Adult patients (age $\\ge 18$ years at admission).
        - Documented invasive mechanical ventilation interval overlapping the ICU stay (verified via item ID `225792`).
        - Length of ICU stay $\\ge T$ hours ($T=24\\text{ h}$ or $T=48\\text{ h}$).
        - Mechanically ventilated by landmark $T$.
        - Documented survival to landmark $T$ (conditioning on survival eliminates immortal-time bias).
        """)

        st.markdown("#### Table: Verified MIMIC-IV v3.1 Clinical Item Identifiers")
        item_data = [
            {"Category": "Vital Sign", "Variable": "Heart Rate", "Item ID": "220045", "MIMIC Dictionary Label": "Heart Rate"},
            {"Category": "Vital Sign", "Variable": "Systolic Blood Pressure", "Item ID": "220179, 220050", "MIMIC Dictionary Label": "Non-invasive / Arterial systolic BP"},
            {"Category": "Vital Sign", "Variable": "Diastolic Blood Pressure", "Item ID": "220180, 220051", "MIMIC Dictionary Label": "Non-invasive / Arterial diastolic BP"},
            {"Category": "Vital Sign", "Variable": "Mean Arterial Pressure", "Item ID": "220181, 220052", "MIMIC Dictionary Label": "Non-invasive / Arterial mean BP"},
            {"Category": "Vital Sign", "Variable": "Respiratory Rate", "Item ID": "220210", "MIMIC Dictionary Label": "Respiratory Rate"},
            {"Category": "Vital Sign", "Variable": "Oxygen Saturation (SpO2)", "Item ID": "220277", "MIMIC Dictionary Label": "O2 saturation pulseoxymetry"},
            {"Category": "Vital Sign", "Variable": "Body Temperature", "Item ID": "223762, 223761", "MIMIC Dictionary Label": "Temperature Celsius / Fahrenheit"},
            {"Category": "Laboratory", "Variable": "Lactate", "Item ID": "50813", "MIMIC Dictionary Label": "Lactate"},
            {"Category": "Laboratory", "Variable": "Creatinine", "Item ID": "50912", "MIMIC Dictionary Label": "Creatinine"},
            {"Category": "Laboratory", "Variable": "Blood Urea Nitrogen (BUN)", "Item ID": "51006", "MIMIC Dictionary Label": "Urea Nitrogen"},
            {"Category": "Laboratory", "Variable": "White Blood Cells (WBC)", "Item ID": "51301", "MIMIC Dictionary Label": "White Blood Cells"},
            {"Category": "Laboratory", "Variable": "Hemoglobin", "Item ID": "51222", "MIMIC Dictionary Label": "Hemoglobin"},
            {"Category": "Laboratory", "Variable": "Platelets", "Item ID": "51265", "MIMIC Dictionary Label": "Platelet Count"},
            {"Category": "Laboratory", "Variable": "Sodium", "Item ID": "50983", "MIMIC Dictionary Label": "Sodium"},
            {"Category": "Laboratory", "Variable": "Potassium", "Item ID": "50971", "MIMIC Dictionary Label": "Potassium"},
            {"Category": "Laboratory", "Variable": "Bicarbonate", "Item ID": "50882", "MIMIC Dictionary Label": "Bicarbonate"},
            {"Category": "Laboratory", "Variable": "Glucose", "Item ID": "50931", "MIMIC Dictionary Label": "Glucose"},
            {"Category": "Laboratory", "Variable": "Total Bilirubin", "Item ID": "50885", "MIMIC Dictionary Label": "Bilirubin, Total"},
            {"Category": "Laboratory", "Variable": "Blood pH", "Item ID": "50820", "MIMIC Dictionary Label": "pH"},
            {"Category": "Laboratory", "Variable": "Chloride", "Item ID": "50902", "MIMIC Dictionary Label": "Chloride"},
            {"Category": "Procedure", "Variable": "Invasive Ventilation", "Item ID": "225792", "MIMIC Dictionary Label": "Invasive Ventilation"}
        ]
        st.dataframe(pd.DataFrame(item_data), use_container_width=True, height=280)

        st.markdown("""
        #### 2. Feature Configurations & Ablation Architecture
        - **Base (43 Predictors):** Demographics (age, gender, ventilation duration, admission type, first care unit), 7 vital-sign aggregations (last, mean, min, max), and latest laboratory values without staleness.
        - **TLS (56 Predictors):** Base feature set plus 13 explicit Targeted Laboratory Staleness features ($s_j$) with $2T$ sentinel encoding.
        - **Missingness (56 Predictors):** Base feature set plus 13 binary missingness indicator variables ($m_j \\in \\{0, 1\\}$).
        - **Both (69 Predictors):** Base feature set + 13 staleness features + 13 missingness indicators.
        
        #### 3. Patient-Level Data Partitioning (Strict Separation)
        To prevent optimistic data leakage across repeated ICU stays, all splits were executed strictly at the unique patient level (`subject_id`):
        """)
        
        split_table = [
            {"Partition": "Training Set", "T=24h Count": "14,992 (64%)", "T=48h Count": "10,925 (64%)", "Role": "Model fitting and parameter optimization"},
            {"Partition": "Validation Set", "T=24h Count": "3,749 (16%)", "T=48h Count": "2,732 (16%)", "Role": "Hyperparameter tuning and early stopping"},
            {"Partition": "Held-Out Test Set", "T=24h Count": "4,686 (20%)", "T=48h Count": "3,415 (20%)", "Role": "Untouched benchmark evaluation & bootstrap testing"}
        ]
        st.table(pd.DataFrame(split_table))

    # ─── TAB 3: BENCHMARK RESULTS & STATISTICS ────────────────────────────────
    with tab3:
        st.markdown("""
        ### Empirical Benchmark Results on MIMIC-IV
        All evaluation was conducted on the untouched held-out test partitions using **1,000 paired patient-level bootstrap resamples** 
        to obtain non-parametric 95% percentile confidence intervals.
        
        #### Table 1: Discrimination & Calibration on Held-Out Test Set
        """)

        metrics_data = [
            {"Horizon": "T = 24 h", "Model": "L2 Logistic Regression", "AUROC (95% CI)": "0.838 [0.821, 0.854]", "AUPRC (95% CI)": "0.500 [0.462, 0.540]", "Brier Score": "0.095 [0.088, 0.101]", "Cal. Slope": "0.938 [0.859, 1.022]", "Cal. Intercept": "-0.086 [-0.245, 0.070]"},
            {"Horizon": "T = 24 h", "Model": "LightGBM (TLS)", "AUROC (95% CI)": "0.867 [0.854, 0.881]", "AUPRC (95% CI)": "0.557 [0.519, 0.596]", "Brier Score": "0.088 [0.082, 0.094]", "Cal. Slope": "0.917 [0.854, 0.987]", "Cal. Intercept": "-0.026 [-0.156, 0.101]"},
            {"Horizon": "T = 48 h", "Model": "L2 Logistic Regression", "AUROC (95% CI)": "0.819 [0.803, 0.837]", "AUPRC (95% CI)": "0.531 [0.490, 0.573]", "Brier Score": "0.109 [0.102, 0.117]", "Cal. Slope": "1.096 [1.007, 1.198]", "Cal. Intercept": "0.167 [0.001, 0.341]"},
            {"Horizon": "T = 48 h", "Model": "LightGBM (TLS)", "AUROC (95% CI)": "0.859 [0.845, 0.873]", "AUPRC (95% CI)": "0.586 [0.545, 0.628]", "Brier Score": "0.102 [0.095, 0.109]", "Cal. Slope": "1.055 [0.985, 1.134]", "Cal. Intercept": "0.179 [0.029, 0.337]"}
        ]
        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)

        st.markdown("""
        #### Table 2: Paired Bootstrap Differences (TLS Minus Base Model, B = 1,000)
        """)
        delta_data = [
            {"Horizon": "T = 24 h", "Model": "Logistic Regression", "Metric": "AUROC", "Base": "0.8267", "TLS": "0.8375", "Difference": "+0.0108", "95% Bootstrap CI": "[+0.0042, +0.0174]", "p-value": "0.0020", "Significance": "Statistically Significant"},
            {"Horizon": "T = 24 h", "Model": "Logistic Regression", "Metric": "AUPRC", "Base": "0.4903", "TLS": "0.4999", "Difference": "+0.0096", "95% Bootstrap CI": "[+0.0011, +0.0182]", "p-value": "0.0420", "Significance": "Nominally Significant"},
            {"Horizon": "T = 24 h", "Model": "LightGBM", "Metric": "AUROC", "Base": "0.8653", "TLS": "0.8672", "Difference": "+0.0019", "95% Bootstrap CI": "[-0.0021, +0.0059]", "p-value": "0.3477", "Significance": "Not Significant"},
            {"Horizon": "T = 48 h", "Model": "LightGBM", "Metric": "AUROC", "Base": "0.8506", "TLS": "0.8595", "Difference": "+0.0089", "95% Bootstrap CI": "[+0.0028, +0.0151]", "p-value": "0.0060", "Significance": "Statistically Significant"},
            {"Horizon": "T = 48 h", "Model": "Logistic Regression", "Metric": "AUROC", "Base": "0.8143", "TLS": "0.8195", "Difference": "+0.0052", "95% Bootstrap CI": "[-0.0031, +0.0135]", "p-value": "0.2218", "Significance": "Not Significant"}
        ]
        st.dataframe(pd.DataFrame(delta_data), use_container_width=True)

        st.markdown("""
        #### Key Clinical Takeaways:
        1. **Model- and Horizon-Dependent Gains:** TLS does not provide a universal, uniform boost across all settings. Instead, measurement recency acts differently on linear versus tree ensembles. At $T=24\\text{ h}$, staleness yields significant discrimination improvement in Logistic Regression ($+0.0108$ AUROC, $p=0.0020$). At $T=48\\text{ h}$, staleness yields significant improvement in LightGBM ($+0.0089$ AUROC, $p=0.0060$).
        2. **TreeSHAP Feature Attribution:** TreeSHAP analysis revealed `bilirubin_staleness` among the **top 5 most influential features** in the entire model, outranking standard absolute lab values such as creatinine, sodium, and platelets.
        3. **Decision Curve Analysis (DCA):** Across clinical threshold probabilities ranging from 0.05 to 0.50, the TLS-augmented LightGBM model demonstrated superior net clinical benefit compared to treat-all and treat-none intervention strategies.
        """)

    # ─── TAB 4: RISK ANALYSIS & GOVERNANCE ────────────────────────────────────
    with tab4:
        st.markdown("""
        ### Risk Analysis, Mitigations & Ethical Governance
        
        #### 1. Methodological Risk Matrix (Table 9.1)
        """)

        risk_matrix = [
            {"Identified Risk": "Data Leakage", "Clinical/Technical Consequence": "Overly optimistic evaluation if future data enters predictors", "Enforced Mitigation Strategy": "Timestamp leakage guard strictly enforces $t \\le T$. Post-landmark injection audits confirm zero feature matrix shift."},
            {"Identified Risk": "Immortal-Time Bias", "Clinical/Technical Consequence": "Including patients who died before prediction artificially inflates discrimination", "Enforced Mitigation Strategy": "Cohort conditioned strictly on survival to landmark $T$; all excluded patients documented in cohort flow."},
            {"Identified Risk": "Class Imbalance Distortions", "Clinical/Technical Consequence": "Artificial weighting alters probability calibration scale", "Enforced Mitigation Strategy": "Class weighting disabled; models trained on natural clinical prevalence (14.2% - 17.1%) with AUPRC and Brier score tracking."},
            {"Identified Risk": "Overfitting on Sentinels", "Clinical/Technical Consequence": "Tree models latching onto synthetic imputation values", "Enforced Mitigation Strategy": "4-way ablation analysis systematically comparing sentinel staleness vs missingness indicators vs combination."},
            {"Identified Risk": "Calibration Misalignment", "Clinical/Technical Consequence": "Probabilities drift from observed ICU death rates", "Enforced Mitigation Strategy": "Calibration slopes and intercepts computed with non-parametric bootstrap intervals; LOWESS reliability curves reported."}
        ]
        st.dataframe(pd.DataFrame(risk_matrix), use_container_width=True)

        st.markdown("""
        #### 2. Data Governance & Ethical Compliance
        - **Database:** MIMIC-IV version 3.1, distributed via PhysioNet under the Health Insurance Portability and Accountability Act (HIPAA) Safe Harbor provision.
        - **Ethical Review:** Secondary analysis of existing de-identified clinical records involving no direct patient contact, clinical trial recruitment, or intervention.
        - **PhysioNet Credentialing:** Research team members completed the mandatory human-subjects research training (CITI Program / Data or Specimens Only Research) and signed the MIMIC-IV Data Use Agreement (DUA).
        - **Redistribution Policy:** No protected health information (PHI) or raw patient records are stored or redistributed. All public CDSS demonstrations utilize synthesized clinical records conforming to the feature schema.
        """)

    # ─── TAB 5: TEAM & ACADEMIC RECORD ────────────────────────────────────────
    with tab5:
        st.markdown("""
        ### Academic Project Record & Authorship
        
        **Institution:**  
        **D. Y. Patil Education Society (Deemed to be University), Kolhapur**  
        School of Engineering and Management | Department of Computer Science & Engineering  
        Academic Year: 2026-27 | Course: Project (`23CSEU7J12`)
        
        ---
        
        #### Research Team & Investigators
        """)

        team_records = [
            {"Name": "Karan Patil", "PRN": "2023025123", "Project Role": "Lead ML Researcher & Manuscript Author", "Institutional Email": "karanpatil.semco25@dypgroup.edu.in", "Training Status": "CITI Completed / DUA Signed"},
            {"Name": "Sarthak Kumbhar", "PRN": "2023025086", "Project Role": "Data Engineering & Cohort Architecture", "Institutional Email": "sarthakkumbhar.semco23@dypgroup.edu.in", "Training Status": "CITI Completed / DUA Signed"},
            {"Name": "Sumaira Shaik", "PRN": "2023025176", "Project Role": "Pipeline Validation, Testing & Integrity", "Institutional Email": "SumeraShaikh.semco23@dypgroup.edu.in", "Training Status": "CITI Completed / DUA Registered"},
            {"Name": "Krishna Hasare", "PRN": "2023025050", "Project Role": "CDSS Dashboard Architecture & System Integration", "Institutional Email": "krishnahasare.semco25@dypgroup.edu.in", "Training Status": "CITI Completed / DUA Registered"}
        ]
        st.table(pd.DataFrame(team_records))

        st.markdown("""
        #### Faculty Supervision & Institutional Leadership
        - **Project Guide:** **Mrs. Archana Sawant**, Assistant Professor, Department of Computer Science & Engineering
        - **Head of Department:** **Dr. G. V. Otari**, Department of Computer Science & Engineering
        - **Director, DYPSEM:** **Dr. A. S. Patil**, School of Engineering and Management
        
        ---
        
        #### Target Journal Publications & Reporting Standards
        - **Primary Submission Target:** *Computers in Biology and Medicine* (Elsevier, Q1, IF: 7.7) / *BMC Medical Informatics and Decision Making*
        - **Secondary Submission Target:** *Scientific Reports* (Nature Portfolio)
        - **Reporting Guideline:** Fully conforming to the **TRIPOD+AI** (*Transparent Reporting of a multivariable prediction model of an Individual Prognosis Or Diagnosis + Artificial Intelligence*) standard.
        """)

    # ─── TAB 6: CDSS USER MANUAL ──────────────────────────────────────────────
    with tab6:
        st.markdown("""
        ### Clinical Decision Support System (CDSS) User Manual
        
        #### 1. Software Environment & Execution Requirements
        - **Runtime Platform:** Python 3.12+ (64-bit) on Windows / Linux / macOS.
        - **Core Dependencies:** `streamlit`, `lightgbm`, `scikit-learn`, `pandas`, `numpy`, `plotly`, `statsmodels`, `joblib`.
        - **Repository Launch Command:**
          ```bash
          # From project root directory
          streamlit run dashboard/app.py
          ```
        
        #### 2. Operational Workbench Guide
        The AURA-ICU dashboard interface provides 6 dedicated clinical workbenches:
        
        1. **Ventilator Telemetry Console:**
           - Real-time pressure-time, flow-time, and volume-time waveform rendering.
           - Ventilator mode indicators (VCV, PCV, SIMV, PSV) and driving pressure telemetry ($P_{\\text{plat}} - \\text{PEEP}$).
           - Rapid Shallow Breathing Index (RSBI) computation and automated weaning readiness alerts.
        
        2. **Clinical Dossiers & AI Inference:**
           - Patient-specific electronic health record summary.
           - Active probability inference display from the calibrated LightGBM model.
           - Multi-tier mortality risk classification (Low, Moderate, High, Critical).
        
        3. **Central Nursing Station (10 Beds):**
           - High-level overview of an entire intensive care unit ward.
           - Dynamic risk sorting to triage highest-acuity patients requiring immediate bedside attention.
           - At-a-glance visualization of stale biomarker counts per bed.
        
        4. **Diagnostic & Biomarker Monitor:**
           - Interactive staleness heatmap across all 13 monitored laboratory biomarkers.
           - Color-coded recency indicators: Fresh ($<6\\text{ h}$), Moderate ($6-20\\text{ h}$), Stale ($20-48\\text{ h}$), Sentinel ($\\ge 48\\text{ h}$).
           - Historical trend trajectories and vital-sign distribution ranges.
        
        5. **Counterfactual Simulation Lab ("What-If"):**
           - Interactive slider panel allowing clinicians to simulate the effect of re-ordering stale lab tests.
           - Demonstrates how acquiring a fresh arterial blood gas or lactate dynamically recalibrates predicted mortality risk.
        
        6. **Clinical Specification & Protocol (This Section):**
           - Complete academic documentation, statistical records, cohort derivation flow, and institutional governance.
        
        #### 3. Clinical Safety & Demonstrational Disclaimer
        > **Academic Demonstration Notice:** This dashboard is an academic research prototype developed strictly for 
        > engineering evaluation and educational demonstration. It is NOT certified as a medical device and is NOT intended 
        > for direct clinical diagnosis, patient management, or bedside treatment decisions.
        """)

    st.markdown("---")
    st.caption("AURA-ICU CDSS | Department of Computer Science & Engineering, DYPSEM Kolhapur | Project 23CSEU7J12")
