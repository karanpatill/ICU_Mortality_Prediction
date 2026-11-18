# app.py - AURA-ICU: Dynamic Clinical Decision Support System
# Main Streamlit Application Entry Point
# D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur
# Authors: Karan Patil, Sarthak Kumbhar, Sumaira Shaik, Krishna Hasare

import sys
import os

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import streamlit as st
from pathlib import Path

# ─── Page Config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="AURA-ICU | Clinical Decision Support System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "AURA-ICU v1.0 | ICU Mortality Prediction via Targeted Laboratory Staleness\n"
            "D. Y. Patil School of Engineering and Management, Kolhapur\n"
            "MIMIC-IV Dataset | LightGBM | AUROC: 0.8559"
        )
    }
)

# ─── Load CSS ────────────────────────────────────────────────────────────────
CSS_PATH = Path(__file__).parent / "assets" / "style.css"
if CSS_PATH.exists():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Import Components ────────────────────────────────────────────────────────
# Add dashboard dir to sys.path for components import
DASHBOARD_DIR = Path(__file__).parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from components.ward_view import render_ward_view
from components.patient_monitor import render_patient_monitor
from components.whatif_sim import render_whatif_sim
from components.documentation import render_documentation

# ─── Session State Init ───────────────────────────────────────────────────────
if "selected_bed_idx" not in st.session_state:
    st.session_state.selected_bed_idx = 0
if "go_to_monitor" not in st.session_state:
    st.session_state.go_to_monitor = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px 0;">
        <div style="font-size:1.6rem;font-weight:800;color:#58a6ff;letter-spacing:3px;">
            AURA-ICU
        </div>
        <div style="font-size:0.65rem;color:#8b949e;letter-spacing:2px;margin-top:2px;">
            CLINICAL DECISION SUPPORT
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation
    st.markdown('<p style="font-size:0.65rem;color:#8b949e;font-weight:700;letter-spacing:2px;">NAVIGATION</p>',
                unsafe_allow_html=True)

    nav_options = [
        "🏥  Virtual ICU Ward",
        "📊  Patient Monitor",
        "🔬  What-If Simulator",
        "📋  Documentation",
    ]
    # If user clicked "View Patient" button from ward, switch to monitor tab
    if st.session_state.get("go_to_monitor", False):
        st.session_state.active_tab = 1
        st.session_state.go_to_monitor = False

    selected_nav = st.radio(
        "Navigate to",
        nav_options,
        index=st.session_state.active_tab,
        label_visibility="collapsed",
        key="nav_radio"
    )
    st.session_state.active_tab = nav_options.index(selected_nav)

    st.divider()

    # Model stats in sidebar
    st.markdown('<p style="font-size:0.65rem;color:#8b949e;font-weight:700;letter-spacing:2px;">MODEL STATS</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;flex-direction:column;gap:6px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">Algorithm</span>
            <span style="font-size:0.72rem;color:#e6edf3;font-weight:600;">LightGBM</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">AUROC</span>
            <span style="font-size:0.72rem;color:#3fb950;font-weight:600;">0.8559</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">AUPRC</span>
            <span style="font-size:0.72rem;color:#3fb950;font-weight:600;">0.5854</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">p-value</span>
            <span style="font-size:0.72rem;color:#3fb950;font-weight:600;">&lt; 0.0001</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">Patients</span>
            <span style="font-size:0.72rem;color:#e6edf3;font-weight:600;">23,367</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">Features</span>
            <span style="font-size:0.72rem;color:#e6edf3;font-weight:600;">52</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.72rem;color:#8b949e;">Inference</span>
            <span style="font-size:0.72rem;color:#3fb950;font-weight:600;">&lt; 1ms</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Staleness legend
    st.markdown('<p style="font-size:0.65rem;color:#8b949e;font-weight:700;letter-spacing:2px;">STALENESS SCALE</p>',
                unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;flex-direction:column;gap:4px;font-size:0.72rem;">
        <div><span style="color:#3fb950;font-weight:700;">&#9679; FRESH</span>
             <span style="color:#8b949e;"> &lt; 6 hours</span></div>
        <div><span style="color:#d29922;font-weight:700;">&#9679; MODERATE</span>
             <span style="color:#8b949e;"> 6-20 hours</span></div>
        <div><span style="color:#f85149;font-weight:700;">&#9679; STALE</span>
             <span style="color:#8b949e;"> 20-48 hours</span></div>
        <div><span style="color:#6e7681;font-weight:700;">&#9632; SENTINEL</span>
             <span style="color:#8b949e;"> &ge;48 hours</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Institution
    st.markdown("""
    <div style="font-size:0.62rem;color:#6e7681;text-align:center;line-height:1.5;">
        D. Y. Patil School of Engineering<br>
        and Management<br>
        (Deemed-to-be-University), Kolhapur<br><br>
        <span style="color:#30363d;">&#8212;</span> B.E. Capstone 2026 <span style="color:#30363d;">&#8212;</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Main Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="aura-header">
    <div>
        <h1 class="aura-title">AURA-ICU</h1>
        <p class="aura-subtitle">
            ADAPTIVE UNCERTAINTY-AWARE RISK ASSESSMENT FOR INTENSIVE CARE UNITS
        </p>
        <p style="font-size:0.72rem;color:#6e7681;margin:4px 0 0 0;">
            Targeted Laboratory Staleness Framework &bull; MIMIC-IV v3.1 &bull;
            LightGBM &bull; 23,367 Patients
        </p>
    </div>
    <div style="text-align:right;">
        <div class="aura-badge">SYSTEM ONLINE</div>
        <div style="font-size:0.65rem;color:#8b949e;margin-top:6px;">
            Fully Offline &bull; Real-time Inference
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Route to Selected Tab ────────────────────────────────────────────────────
active_idx = st.session_state.active_tab

if active_idx == 0:
    render_ward_view()
elif active_idx == 1:
    render_patient_monitor()
elif active_idx == 2:
    render_whatif_sim()
elif active_idx == 3:
    render_documentation()

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#21262d;margin-top:40px;">
<div style="text-align:center;padding:12px;font-size:0.68rem;color:#6e7681;">
    AURA-ICU v1.0 &bull;
    D. Y. Patil School of Engineering and Management, Kolhapur &bull;
    Karan Patil &bull; Sarthak Kumbhar &bull; Sumaira Shaik &bull; Krishna Hasare<br>
    <span style="font-size:0.6rem;">
        For academic demonstration only. Not for clinical use.
        MIMIC-IV data: Johnson et al., Scientific Data 2023.
    </span>
</div>
""", unsafe_allow_html=True)
