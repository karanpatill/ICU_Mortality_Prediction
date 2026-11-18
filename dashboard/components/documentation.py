# documentation.py - Project Documentation Tab
# AURA-ICU: Dynamic Clinical Decision Support System

import streamlit as st
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def render_documentation():
    """Render project documentation and methodology."""

    st.markdown("""
    <div style="margin-bottom:16px;">
        <span class="section-header">PROJECT DOCUMENTATION & METHODOLOGY</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Project Overview", "Methodology", "Model Details", "Team & Paper"
    ])

    with tab1:
        st.markdown("""
        ## AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for ICU

        **AURA-ICU** is a Clinical Decision Support System (CDSS) built as part of a
        Final Year B.E. Capstone Project at D. Y. Patil School of Engineering and
        Management (Deemed-to-be-University), Kolhapur.

        ### Problem Statement
        In ICU settings, clinicians face **information staleness** — lab results may be
        hours or days old when decisions are made. Standard ML models treat a creatinine
        value measured 2 hours ago the same as one measured 40 hours ago. This is
        clinically incorrect.

        ### Our Innovation: Targeted Laboratory Staleness (TLS)
        We introduce **staleness as an explicit feature** — encoding *how long ago*
        each lab measurement was taken alongside its value. This allows the model to
        quantify uncertainty due to measurement recency.

        ### Key Results
        | Metric | Baseline (Values Only) | TLS Model (Values + Staleness) | Improvement |
        |--------|----------------------|-------------------------------|-------------|
        | AUROC  | 0.8527               | **0.8559**                    | +0.319%     |
        | AUPRC  | 0.5812               | **0.5854**                    | +0.415%     |
        | Brier  | —                    | 0.0984                        | —           |
        | p-value| —                    | < 0.0001 (bootstrap n=1000)   | Significant |

        ### Dataset: MIMIC-IV v3.1
        - **23,367** mechanically ventilated adult ICU patients
        - **17.2%** mortality rate (4,019 deaths)
        - 13 laboratory biomarkers + staleness values
        - Source: Beth Israel Deaconess Medical Center, Boston, MA
        """)

    with tab2:
        st.markdown("""
        ## Methodology

        ### 1. Cohort Selection
        ```
        MIMIC-IV v3.1 Database
            → Filter: Adult patients (age ≥ 18)
            → Filter: Mechanically ventilated (IMV)
            → Window: First 24 hours of ICU stay
            → Outcome: Hospital mortality (binary)
        ```

        ### 2. Feature Engineering
        **13 Laboratory Biomarkers collected:**
        - Renal: Creatinine, BUN
        - Electrolytes: Potassium, Sodium
        - Metabolic: Glucose, Lactate, Bilirubin
        - Hematology: Platelets, WBC, Hemoglobin
        - Blood Gas: PaO2, PaCO2, pH

        **For each lab, two features created:**
        - `{lab}_val`: Most recent measured value
        - `{lab}_staleness`: Hours since measurement (capped at 48h = Sentinel)

        **Staleness Classification:**
        | Category | Hours | Clinical Meaning |
        |----------|-------|-----------------|
        | Fresh    | < 6h  | Measurement is current |
        | Moderate | 6–20h | Acceptable, monitor |
        | Stale    | 20–48h| Clinically questionable |
        | Sentinel | ≥ 48h | No recent data — high uncertainty |

        ### 3. Encoding
        ```python
        # Exact encoding used in production model:
        df['gender'] = (df['gender'] == 'M').astype(int)
        df = pd.get_dummies(df, columns=['first_careunit', 'admission_type'])
        # Total: 52 features
        ```

        ### 4. Model Training
        - **Algorithm:** LightGBM Gradient Boosted Trees
        - **Hyperparameters:** n_estimators=300, max_depth=6, learning_rate=0.03
        - **Validation:** 5-fold stratified cross-validation
        - **Significance:** Bootstrap resampling (n=1,000 iterations)
        - **Training time:** 0.75 seconds on 12-core CPU
        - **Inference latency:** < 1ms per patient

        ### 5. Statistical Validation
        - Paired bootstrap test (n=1000 bootstraps)
        - 95% Confidence Intervals reported
        - p < 0.0001 for AUROC improvement
        - p = 0.025 for AUPRC improvement
        """)

    with tab3:
        st.markdown("""
        ## Model Technical Details
        """)
        # Load and display schema
        try:
            schema_path = BASE_DIR / "models" / "feature_schema.json"
            with open(schema_path, "r") as f:
                schema = json.load(f)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Model Family", schema.get("model_family", "LightGBM"))
                st.metric("Total Features", schema.get("n_features", 52))
                st.metric("Sentinel Threshold", f"{schema.get('sentinel_value_hours', 48)}h")
                st.metric("Estimators", schema.get("n_estimators", 300))

            with col2:
                metrics = schema.get("metrics", {})
                st.metric("AUROC", f"{metrics.get('auroc', 0.8559):.4f}")
                st.metric("AUPRC", f"{metrics.get('auprc', 0.5854):.4f}")
                st.metric("Brier Score", f"{metrics.get('brier_score', 0.0984):.4f}")
                st.metric("p-value (AUROC)", metrics.get("auroc_p_value", "< 0.0001"))

            st.markdown("### Feature List (52 Features)")
            features = schema.get("features", [])
            feat_df_data = {
                "Feature": features,
                "Type": ["Staleness" if f.endswith("_staleness")
                         else ("Lab Value" if f.endswith("_val")
                               else ("Demographic" if f in ["age", "gender", "vent_duration_hours"]
                                     else "Categorical Encoding"))
                         for f in features]
            }
            import pandas as pd
            feat_df = pd.DataFrame(feat_df_data)
            st.dataframe(feat_df, use_container_width=True, height=300)

        except Exception as e:
            st.warning(f"Could not load schema: {e}")

        st.markdown("""
        ### Why LightGBM?
        - **Speed:** 300x faster than XGBoost on tabular data
        - **Missing value handling:** Native support for NaN (sentinel values)
        - **Feature importance:** Built-in split-based importance (no SHAP needed)
        - **Calibration:** Probability outputs are well-calibrated for clinical use
        - **Interpretability:** Each prediction traceable to individual features

        ### Model File
        ```
        D:\\ICU_Mortality_Prediction\\models\\lightgbm_staleness_production.joblib
        Size: ~1 MB | Fully offline | No internet required
        ```
        """)

    with tab4:
        st.markdown("""
        ## Project Team

        | Name | Role | Email |
        |------|------|-------|
        | **Karan Patil** | ML Lead & Paper Author | karanpatil.semco25@dypgroup.edu.in |
        | **Sarthak Kumbhar** | Data Engineering | sarthakkumbhar.semco23@dypgroup.edu.in |
        | **Sumaira Shaik** | Validation & Testing | SumeraShaikh.semco23@dypgroup.edu.in |
        | **Krishna Hasare** | Dashboard & Integration | krishnahasare.semco25@dypgroup.edu.in |

        **Institution:** D. Y. Patil School of Engineering and Management
        (Deemed-to-be-University), Kolhapur

        ---

        ## Research Paper

        **Title:** "Targeted Laboratory Staleness as a Mortality Predictor in
        Mechanically Ventilated ICU Patients: A MIMIC-IV Analysis"

        **Journal/Preprint:** medRxiv (Submitted November 2026)

        **DOI:** Pending (expected within 24-48h of submission)

        ---

        ## Technology Stack

        | Component | Technology |
        |-----------|-----------|
        | ML Model | LightGBM 4.x |
        | Dashboard | Streamlit + Plotly |
        | Data | MIMIC-IV v3.1 (PhysioNet) |
        | Language | Python 3.12 |
        | Paper | Typst (compiled PDF) |
        | Notebook | Jupyter + nbformat |

        ---

        ## Project Structure
        ```
        D:\\ICU_Mortality_Prediction\\
        ├── data\\mimiciv\\           # MIMIC-IV dataset (23,367 patients)
        ├── models\\                 # Trained model + feature schema
        ├── research-paper\\         # Typst source + compiled PDF
        ├── dashboard\\              # This CDSS application
        ├── experiments\\            # Benchmark scripts
        └── ICU_Mortality_Prediction_Master_Pipeline.ipynb
        ```

        ---

        ## Ethical Statement
        > This dashboard is built for academic demonstration purposes using the
        > de-identified MIMIC-IV database (PhysioNet). It is NOT intended for
        > direct clinical decision-making. All patient identifiers have been
        > removed per MIMIC data use agreement. The model should undergo
        > prospective clinical validation before any real-world deployment.

        ---

        ## Acknowledgements
        - MIMIC-IV database: Johnson et al., Scientific Data 2023
        - PhysioNet: Goldberger et al., Circulation 2000
        - LightGBM: Ke et al., NeurIPS 2017
        """)
