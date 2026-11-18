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
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Load Custom Medical Console CSS ──────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).parent
CSS_PATH = DASHBOARD_DIR / "assets" / "style.css"
if CSS_PATH.exists():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Path injection for modular components
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from components.ventilator_screen import render_ventilator_screen
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

# ─── Sidebar Navigation & System Telemetry ────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 16px 0; border-bottom: 1px solid #1c2738; margin-bottom: 14px;">
        <div style="font-family: 'Chakra Petch', sans-serif; font-size: 1.5rem; font-weight: 700; color: #ffffff; letter-spacing: 2px;">
            AURA-ICU
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #00e5ff; letter-spacing: 1.5px; text-transform: uppercase;">
            CLINICAL DECISION SUPPORT SYSTEM
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.60rem; color: #718096; margin-top: 4px;">
            Targeted Laboratory Staleness v3.1
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "BEDSIDE VENTILATOR CONSOLE",
        "CENTRAL NURSING STATION (12 BEDS)",
        "INPATIENT DIAGNOSTIC MONITOR",
        "COUNTERFACTUAL INTERVENTION LAB",
        "CLINICAL SPECIFICATION & PAPER"
    ]

    # Handle direct navigation jumps from ward view
    if st.session_state.get("go_to_monitor", False):
        st.session_state.active_nav_index = 2
        st.session_state.go_to_monitor = False

    selected_nav = st.radio(
        "OPERATIONAL WORKBENCH",
        nav_options,
        index=st.session_state.active_nav_index,
        label_visibility="collapsed"
    )
    st.session_state.active_nav_index = nav_options.index(selected_nav)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Telemetry Specs
    st.markdown("""
    <div style="background: #080d14; border: 1px solid #1c2738; border-radius: 4px; padding: 10px 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;">
        <div style="color: #718096; text-transform: uppercase; margin-bottom: 6px; font-weight: 700; border-bottom: 1px solid #142030; padding-bottom: 4px;">
            SYSTEM TELEMETRY
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
            <span style="color: #718096;">INFERENCE ENGINE</span>
            <span style="color: #00ff66; font-weight: 700;">LightGBM GBDT</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
            <span style="color: #718096;">AUROC</span>
            <span style="color: #00ff66; font-weight: 700;">0.8559 (p&lt;0.0001)</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
            <span style="color: #718096;">LATENCY</span>
            <span style="color: #00ff66; font-weight: 700;">&lt; 1.0 ms</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
            <span style="color: #718096;">ACTIVE COHORT</span>
            <span style="color: #edf2f7;">23,367 Patients</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span style="color: #718096;">SENTINEL THRESHOLD</span>
            <span style="color: #edf2f7;">48.0 Hours</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; color: #4a5568; line-height: 1.5; text-align: center;">
        D. Y. PATIL SCHOOL OF ENGINEERING & MANAGEMENT<br>
        (DEEMED-TO-BE-UNIVERSITY), KOLHAPUR<br>
        DEPARTMENT OF COMPUTER ENGINEERING
    </div>
    """, unsafe_allow_html=True)

# ─── Dispatch to Active Workbench ─────────────────────────────────────────────
idx = st.session_state.active_nav_index

if idx == 0:
    render_ventilator_screen()
elif idx == 1:
    render_ward_view()
elif idx == 2:
    render_patient_monitor()
elif idx == 3:
    render_whatif_sim()
elif idx == 4:
    render_documentation()
