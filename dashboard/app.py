# app.py - AURA-ICU: Dynamic Clinical Decision Support System
# Main Streamlit Application Entry Point
# D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur
# Authors: Karan Patil, Sarthak Kumbhar, Sumaira Shaik, Krishna Hasare

import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import streamlit as st

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AURA-ICU | Clinical Decision Support System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Load Custom Clean Healthcare CSS ─────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).parent
CSS_PATH = DASHBOARD_DIR / "assets" / "style.css"
if CSS_PATH.exists():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Path injection for modular components
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from components.ventilator_screen import render_ventilator_screen
from components.clinical_dossier import render_clinical_dossier
from components.ward_view import render_ward_view
from components.patient_monitor import render_patient_monitor
from components.whatif_sim import render_whatif_sim
from components.documentation import render_documentation

# ─── Session State Initialization ─────────────────────────────────────────────
if "selected_bed_idx" not in st.session_state:
    st.session_state.selected_bed_idx = 0
if "go_to_monitor" not in st.session_state:
    st.session_state.go_to_monitor = False
if "active_nav_index" not in st.session_state:
    st.session_state.active_nav_index = 0

# ─── Sidebar Navigation & Clinical Telemetry ──────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 AURA-ICU")
    st.caption("Clinical Decision Support System &bull; Targeted Laboratory Staleness")
    st.divider()

    nav_options = [
        "🫁 Bedside ICU Ventilator Console",
        "📋 10 Patient Dossiers & On-Demand AI",
        "🏥 Central Nursing Station (10 Beds)",
        "🔬 Inpatient Diagnostic Monitor",
        "🧪 Counterfactual Intervention Lab",
        "📄 Clinical Specification & Paper"
    ]

    if st.session_state.get("go_to_monitor", False):
        st.session_state.active_nav_index = 3
        st.session_state.go_to_monitor = False

    selected_nav = st.radio(
        "OPERATIONAL WORKBENCH",
        nav_options,
        index=st.session_state.active_nav_index,
        label_visibility="collapsed"
    )
    st.session_state.active_nav_index = nav_options.index(selected_nav)

    st.divider()

    st.markdown("#### 📊 Model Telemetry")
    st.write("**Model:** LightGBM GBDT (300 Trees)")
    st.write("**Validation AUROC:** `0.8559` (p < 0.0001)")
    st.write("**Inference Latency:** `< 1.0 ms`")
    st.write("**Cohort:** 23,367 MIMIC-IV Patients")
    st.write("**Sentinel Value:** `48.0 Hours`")

    st.divider()

    st.caption(
        "D. Y. PATIL SCHOOL OF ENGINEERING & MANAGEMENT\n\n"
        "(DEEMED-TO-BE-UNIVERSITY), KOLHAPUR\n\n"
        "Department of Computer Engineering &bull; B.E. Capstone 2026"
    )

# ─── Dispatch to Active Workbench ─────────────────────────────────────────────
idx = st.session_state.active_nav_index

if idx == 0:
    render_ventilator_screen()
elif idx == 1:
    render_clinical_dossier()
elif idx == 2:
    render_ward_view()
elif idx == 3:
    render_patient_monitor()
elif idx == 4:
    render_whatif_sim()
elif idx == 5:
    render_documentation()
