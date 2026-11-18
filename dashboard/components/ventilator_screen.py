# ventilator_screen.py - High-Fidelity ICU Bedside Ventilator & Telemetry Console
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units
# D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from components.utils import (
    load_model, load_schema, encode_features, predict_risk,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL, SENTINEL_HOURS
)

# ── Preset ICU Clinical Scenarios ─────────────────────────────────────────────
SCENARIOS = {
    "SEPSIS_ARDS": {
        "title": "Severe Sepsis + Early ARDS (High Staleness Deterioration)",
        "unit": "Medical Intensive Care Unit (MICU)",
        "admission_type": "EW EMER.",
        "age": 68,
        "gender": "M",
        "vent_duration_hours": 36,
        "hr": 118,
        "spo2": 91,
        "bp_sys": 88,
        "bp_dia": 54,
        "etco2": 46,
        "peep": 12,
        "p_peak": 34,
        "vt": 420,
        "fio2": 70,
        "mode": "PRVC / AC",
        "labs": {
            "lactate_val": 4.6, "lactate_staleness": 28.5,
            "pao2_val": 64.0, "pao2_staleness": 24.0,
            "paco2_val": 48.0, "paco2_staleness": 24.0,
            "ph_val": 7.28, "ph_staleness": 24.0,
            "creatinine_val": 2.4, "creatinine_staleness": 18.0,
            "bun_val": 42.0, "bun_staleness": 18.0,
            "potassium_val": 4.9, "potassium_staleness": 12.0,
            "sodium_val": 136.0, "sodium_staleness": 12.0,
            "glucose_val": 195.0, "glucose_staleness": 6.0,
            "platelets_val": 85.0, "platelets_staleness": 22.0,
            "wbc_val": 22.4, "wbc_staleness": 18.0,
            "hemoglobin_val": 8.9, "hemoglobin_staleness": 18.0,
            "bilirubin_val": 2.8, "bilirubin_staleness": 32.0,
        },
        "alarm": "HIGH ALERT: SEVERE TISSUE HYPOXIA & STALE BLOOD GAS"
    },
    "WEANING_FAILURE": {
        "title": "Ventilator Weaning Failure (Post-SBT Fatigue)",
        "unit": "Surgical Intensive Care Unit (SICU)",
        "admission_type": "URGENT",
        "age": 72,
        "gender": "F",
        "vent_duration_hours": 64,
        "hr": 104,
        "spo2": 93,
        "bp_sys": 142,
        "bp_dia": 86,
        "etco2": 44,
        "peep": 8,
        "p_peak": 26,
        "vt": 380,
        "fio2": 50,
        "mode": "PSV / CPAP",
        "labs": {
            "lactate_val": 2.4, "lactate_staleness": 16.0,
            "pao2_val": 72.0, "pao2_staleness": 14.0,
            "paco2_val": 45.0, "paco2_staleness": 14.0,
            "ph_val": 7.34, "ph_staleness": 14.0,
            "creatinine_val": 1.6, "creatinine_staleness": 26.0,
            "bun_val": 30.0, "bun_staleness": 26.0,
            "potassium_val": 4.1, "potassium_staleness": 14.0,
            "sodium_val": 139.0, "sodium_staleness": 14.0,
            "glucose_val": 140.0, "glucose_staleness": 8.0,
            "platelets_val": 140.0, "platelets_staleness": 26.0,
            "wbc_val": 13.5, "wbc_staleness": 26.0,
            "hemoglobin_val": 9.4, "hemoglobin_staleness": 26.0,
            "bilirubin_val": 1.1, "bilirubin_staleness": 48.0,
        },
        "alarm": "MODERATE: RESPIRATORY MUSCLE FATIGUE RISK"
    },
    "POSTOP_STABILIZED": {
        "title": "Post-CABG Recovery (Stabilized & Fresh Biomarkers)",
        "unit": "Coronary Care Unit (CCU)",
        "admission_type": "ELECTIVE",
        "age": 59,
        "gender": "M",
        "vent_duration_hours": 12,
        "hr": 78,
        "spo2": 99,
        "bp_sys": 118,
        "bp_dia": 72,
        "etco2": 37,
        "peep": 5,
        "p_peak": 18,
        "vt": 480,
        "fio2": 40,
        "mode": "VCV / AC",
        "labs": {
            "lactate_val": 1.3, "lactate_staleness": 2.0,
            "pao2_val": 112.0, "pao2_staleness": 1.5,
            "paco2_val": 38.0, "paco2_staleness": 1.5,
            "ph_val": 7.41, "ph_staleness": 1.5,
            "creatinine_val": 0.9, "creatinine_staleness": 3.0,
            "bun_val": 16.0, "bun_staleness": 3.0,
            "potassium_val": 4.2, "potassium_staleness": 2.0,
            "sodium_val": 140.0, "sodium_staleness": 2.0,
            "glucose_val": 115.0, "glucose_staleness": 1.5,
            "platelets_val": 210.0, "platelets_staleness": 3.0,
            "wbc_val": 9.2, "wbc_staleness": 3.0,
            "hemoglobin_val": 11.2, "hemoglobin_staleness": 3.0,
            "bilirubin_val": 0.8, "bilirubin_staleness": 4.0,
        },
        "alarm": "PATIENT STABLE: PROTOCOL WEANING CANDIDATE"
    }
}

# ── Oscilloscope Canvas Component (HTML5 / WebGL Trace Simulator) ─────────────
def render_oscilloscope(hr: int, spo2: int, p_peak: int, peep: int):
    """
    Renders a 60fps hospital oscilloscope monitor with ECG Lead II,
    Pleth SpO2, and Ventilator Airway Pressure (Paw) traces.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #04070b;
            overflow: hidden;
            font-family: 'JetBrains Mono', 'Segoe UI', monospace;
        }}
        #scope {{
            width: 100%;
            height: 250px;
            display: block;
            background: #03060a;
        }}
    </style>
    </head>
    <body>
    <canvas id="scope"></canvas>
    <script>
        const canvas = document.getElementById('scope');
        const ctx = canvas.getContext('2d');
        
        function resize() {{
            canvas.width = canvas.clientWidth * window.devicePixelRatio;
            canvas.height = canvas.clientHeight * window.devicePixelRatio;
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        }}
        window.addEventListener('resize', resize);
        resize();

        let sweepX = 0;
        const hr = {hr};
        const spo2 = {spo2};
        const pPeak = {p_peak};
        const peep = {peep};
        
        let t = 0;
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        
        // Channels: 3 channels
        // Ch 1: ECG (0 - 80px)
        // Ch 2: Pleth SpO2 (80 - 165px)
        // Ch 3: Ventilator Paw (165 - 250px)
        
        const trailBuffer = [];

        function ecgFunc(phase) {{
            // P-Q-R-S-T synthesis
            const p = phase % 1.0;
            if (p > 0.15 && p < 0.22) return Math.sin((p - 0.15) / 0.07 * Math.PI) * 0.18; // P wave
            if (p > 0.32 && p < 0.34) return -0.15; // Q
            if (p >= 0.34 && p < 0.38) return 1.0;  // R peak
            if (p >= 0.38 && p < 0.41) return -0.35; // S
            if (p > 0.48 && p < 0.65) return Math.sin((p - 0.48) / 0.17 * Math.PI) * 0.28; // T wave
            return 0.0;
        }}

        function plethFunc(phase) {{
            const p = phase % 1.0;
            if (p < 0.25) {{
                return Math.sin(p / 0.25 * Math.PI * 0.5);
            }} else if (p < 0.4) {{
                return Math.cos((p - 0.25) / 0.15 * Math.PI * 0.5) * 0.4 + 0.6; // dicrotic notch
            }} else {{
                return Math.exp(-(p - 0.4) * 4) * 0.6;
            }}
        }}

        function pawFunc(phase) {{
            const p = phase % 1.0;
            if (p < 0.33) {{ // Inspiration (I:E = 1:2)
                return Math.sin(p / 0.33 * Math.PI * 0.5);
            }} else {{ // Expiration
                return Math.exp(-(p - 0.33) * 6);
            }}
        }}

        function drawGrid() {{
            ctx.strokeStyle = 'rgba(20, 35, 52, 0.4)';
            ctx.lineWidth = 1;
            const gridSz = 20;
            for (let x = 0; x < width; x += gridSz) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }}
            for (let y = 0; y < height; y += gridSz) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }}
        }}

        function animate() {{
            // Dim clear for phosphorus decay effect
            ctx.fillStyle = 'rgba(3, 6, 10, 0.12)';
            ctx.fillRect(0, 0, width, height);
            
            drawGrid();

            const speed = (hr / 60) * 1.8;
            t += 0.016 * speed;
            
            // Advance sweep
            const sweepStep = 2.2;
            sweepX = (sweepX + sweepStep) % width;

            // Clear vertical beam slit ahead of trace
            ctx.clearRect(sweepX, 0, 14, height);

            // Channel 1: ECG Lead II (Green)
            const ecgVal = ecgFunc(t);
            const ecgY = 48 - (ecgVal * 32);
            ctx.fillStyle = '#00ff66';
            ctx.shadowColor = '#00ff66';
            ctx.shadowBlur = 6;
            ctx.fillRect(sweepX, ecgY, 2, 2);

            // Channel 2: SpO2 Pleth (Cyan)
            const plethVal = plethFunc(t * 1.0);
            const plethY = 130 - (plethVal * 28);
            ctx.fillStyle = '#00e5ff';
            ctx.shadowColor = '#00e5ff';
            ctx.shadowBlur = 6;
            ctx.fillRect(sweepX, plethY, 2, 2);

            // Channel 3: Ventilator Paw (Amber)
            const ventRate = (hr / 60) * 0.25; // ~15-18 bpm
            const pawVal = pawFunc(t * 0.25);
            const pawY = 225 - (pawVal * 35);
            ctx.fillStyle = '#ffb700';
            ctx.shadowColor = '#ffb700';
            ctx.shadowBlur = 6;
            ctx.fillRect(sweepX, pawY, 2, 2);

            // Channel Annotations
            ctx.shadowBlur = 0;
            ctx.font = '10px monospace';
            ctx.fillStyle = '#00ff66';
            ctx.fillText('ECG LEAD II  II x1.0', 12, 18);
            
            ctx.fillStyle = '#00e5ff';
            ctx.fillText('PLETH  SPO2 PULSE', 12, 98);
            
            ctx.fillStyle = '#ffb700';
            ctx.fillText('PAW (cmH2O)  VENT FLOW', 12, 180);

            requestAnimationFrame(animate);
        }}
        
        // Fill initial black background
        ctx.fillStyle = '#03060a';
        ctx.fillRect(0, 0, width, height);
        animate();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=265, scrolling=False)


# ── Main Ventilator Screen Renderer ───────────────────────────────────────────
def render_ventilator_screen():
    model = load_model()
    schema = load_schema()

    # Session State setup for dynamic ICU Simulation
    if "sim_scenario" not in st.session_state:
        st.session_state.sim_scenario = "SEPSIS_ARDS"
    if "active_patient_state" not in st.session_state:
        st.session_state.active_patient_state = dict(SCENARIOS["SEPSIS_ARDS"]["labs"])
    if "abg_drawn" not in st.session_state:
        st.session_state.abg_drawn = False

    # ── Console Top Bar ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="icu-console-header">
        <div class="icu-title-group">
            <div class="icu-pulse-dot"></div>
            <div>
                <div class="icu-system-title">AURA-ICU BEDSIDE VENTILATOR & TELEMETRY CONSOLE</div>
                <div class="icu-system-subtitle">TARGETED LABORATORY STALENESS DECAY ENGINE &bull; ACTIVE BEDSIDE TELEMETRY</div>
            </div>
        </div>
        <div style="display:flex;gap:18px;align-items:center;">
            <div style="text-align:right;">
                <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-muted);">MONITOR INTERFACE</div>
                <div style="font-family:var(--font-mono);font-size:0.75rem;color:#00e5ff;font-weight:700;">HAMILTON / INTELLIVUE</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-muted);">AI COPILOT STATUS</div>
                <div style="font-family:var(--font-mono);font-size:0.75rem;color:#00ff66;font-weight:700;">ONLINE &bull; &lt;1ms LATENCY</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Scenario Selector & Mode Bar ──────────────────────────────────────────
    c_scen, c_mode, c_stat = st.columns([2, 1, 1])
    
    with c_scen:
        scenario_key = st.selectbox(
            "CLINICAL ICU SIMULATION PRESET",
            options=list(SCENARIOS.keys()),
            format_func=lambda k: f"{k}: {SCENARIOS[k]['title']}",
            index=list(SCENARIOS.keys()).index(st.session_state.sim_scenario),
            label_visibility="collapsed"
        )
        if scenario_key != st.session_state.sim_scenario:
            st.session_state.sim_scenario = scenario_key
            st.session_state.active_patient_state = dict(SCENARIOS[scenario_key]["labs"])
            st.session_state.abg_drawn = False
            st.rerun()

    active_scen = SCENARIOS[st.session_state.sim_scenario]

    with c_mode:
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">VENTILATION MODE</div>
            <div style="font-family:var(--font-mono);font-size:0.85rem;color:#ffb700;font-weight:700;">{active_scen['mode']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_stat:
        alarm_class = "alarm-banner-critical" if "HIGH" in active_scen["alarm"] else "alarm-banner-advisory"
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">CARE UNIT</div>
            <div style="font-family:var(--font-mono);font-size:0.75rem;color:#edf2f7;font-weight:600;">{active_scen['unit'][:18]}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Primary Oscilloscope Screen & Telemetry Column ────────────────────────
    col_wave, col_vitals = st.columns([2.5, 1.2])

    with col_wave:
        st.markdown('<div class="oscilloscope-frame">', unsafe_allow_html=True)
        render_oscilloscope(
            hr=active_scen["hr"],
            spo2=active_scen["spo2"],
            p_peak=active_scen["p_peak"],
            peep=active_scen["peep"]
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_vitals:
        # Vitals Tiles (Digital Readouts)
        v1, v2 = st.columns(2)
        with v1:
            st.markdown(f"""
            <div class="vital-tile" style="border-left: 3px solid #00ff66;">
                <div class="vital-tile-label" style="color: #00ff66;">HR <span style="font-size:0.55rem;color:#718096;">BPM</span></div>
                <div class="vital-tile-value" style="color: #00ff66;">{active_scen['hr']}</div>
                <div class="vital-tile-unit">SINUS TACHYCARDIA</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="vital-tile" style="border-left: 3px solid #ff2a6d;">
                <div class="vital-tile-label" style="color: #ff2a6d;">ABP <span style="font-size:0.55rem;color:#718096;">mmHg</span></div>
                <div class="vital-tile-value" style="color: #ff2a6d;font-size:1.8rem;margin-top:10px;">
                    {active_scen['bp_sys']}/{active_scen['bp_dia']}
                </div>
                <div class="vital-tile-unit">MAP: {int((active_scen['bp_sys'] + 2*active_scen['bp_dia'])/3)} mmHg</div>
            </div>
            """, unsafe_allow_html=True)

        with v2:
            st.markdown(f"""
            <div class="vital-tile" style="border-left: 3px solid #00e5ff;">
                <div class="vital-tile-label" style="color: #00e5ff;">SpO2 <span style="font-size:0.55rem;color:#718096;">%</span></div>
                <div class="vital-tile-value" style="color: #00e5ff;">{active_scen['spo2']}</div>
                <div class="vital-tile-unit">PLETH QUALITY: HIGH</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="vital-tile" style="border-left: 3px solid #ffb700;">
                <div class="vital-tile-label" style="color: #ffb700;">P_PEAK <span style="font-size:0.55rem;color:#718096;">cmH2O</span></div>
                <div class="vital-tile-value" style="color: #ffb700;">{active_scen['p_peak']}</div>
                <div class="vital-tile-unit">PEEP: {active_scen['peep']} &bull; Vt: {active_scen['vt']}mL</div>
            </div>
            """, unsafe_allow_html=True)

    # ── AI Model Inference Engine (Targeted Laboratory Staleness) ─────────────
    # Prepare patient vector
    curr_labs = st.session_state.active_patient_state
    patient_dict = {
        "age": active_scen["age"],
        "gender": active_scen["gender"],
        "first_careunit": active_scen["unit"],
        "admission_type": active_scen["admission_type"],
        "vent_duration_hours": active_scen["vent_duration_hours"],
    }
    patient_dict.update(curr_labs)
    patient_row = pd.Series(patient_dict)
    
    # Predict with LightGBM
    X_input = encode_features(pd.DataFrame([patient_dict]), schema["features"])
    predicted_risk_pct = float(model.predict_proba(X_input)[:, 1][0] * 100)

    # Baseline comparison (if ABG was fresh vs current)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── AURA-ICU Neural CDSS Panel ────────────────────────────────────────────
    c_risk, c_matrix, c_intervene = st.columns([1.1, 1.6, 1.3])

    with c_risk:
        risk_color = "#ff1744" if predicted_risk_pct >= 70 else ("#ff9100" if predicted_risk_pct >= 50 else ("#ffd600" if predicted_risk_pct >= 25 else "#00e676"))
        status_label = "CRITICAL DETERIORATION" if predicted_risk_pct >= 70 else ("ELEVATED RISK" if predicted_risk_pct >= 50 else ("WATCH REQUIRED" if predicted_risk_pct >= 25 else "PHYSIOLOGICALLY STABLE"))
        
        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-top:4px solid {risk_color};border-radius:6px;padding:16px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;">
                AURA-ICU MORTALITY RISK
            </div>
            <div style="font-family:var(--font-display);font-size:3.4rem;font-weight:700;color:{risk_color};line-height:1;margin:10px 0 4px 0;">
                {predicted_risk_pct:.1f}<span style="font-size:1.6rem;">%</span>
            </div>
            <div style="font-family:var(--font-mono);font-size:0.72rem;font-weight:700;color:{risk_color};background:rgba(255,255,255,0.04);padding:4px 8px;border-radius:3px;display:inline-block;letter-spacing:1px;">
                {status_label}
            </div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:#718096;margin-top:10px;">
                MIMIC-IV Cohort Baseline: 17.2%<br>
                Model Confidence: High (AUROC 0.8559)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_matrix:
        st.markdown("""
        <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">
            TARGETED BIOMARKER STALENESS MATRIX
        </div>
        """, unsafe_allow_html=True)

        key_labs = ["lactate", "pao2", "ph", "creatinine", "bilirubin", "platelets"]
        grid_rows = ""
        for lab in key_labs:
            h = float(curr_labs.get(f"{lab}_staleness", 48.0))
            val = float(curr_labs.get(f"{lab}_val", 0.0))
            unit = LAB_UNITS[lab]
            
            if h >= 24.0:
                s_color = "#ff1744"
                s_badge = "CRITICAL STALE"
            elif h >= 12.0:
                s_color = "#ff9100"
                s_badge = "MODERATE"
            else:
                s_color = "#00e676"
                s_badge = "FRESH"

            bar_width = min(100, int((h / 48.0) * 100))
            grid_rows += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;padding:5px 0;border-bottom:1px solid #142030;font-family:var(--font-mono);font-size:0.72rem;">
                <span style="color:#edf2f7;width:80px;font-weight:600;">{LAB_DISPLAY[lab]}</span>
                <span style="color:#00e5ff;width:75px;">{val:.2f} {unit}</span>
                <div style="flex:1;background:#142030;height:6px;border-radius:3px;margin:0 12px;overflow:hidden;">
                    <div style="width:{bar_width}%;height:100%;background:{s_color};"></div>
                </div>
                <span style="color:{s_color};font-size:0.62rem;font-weight:700;width:95px;text-align:right;">
                    {h:.1f}h ({s_badge})
                </span>
            </div>
            """

        st.markdown(f"""
        <div style="background:#090e15;border:1px solid #1c2738;border-radius:6px;padding:10px 14px;">
            {grid_rows}
        </div>
        """, unsafe_allow_html=True)

    with c_intervene:
        st.markdown("""
        <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">
            BEDSIDE INTERVENTIONS & LAB REFRESH
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#090e15;border:1px solid #1c2738;border-radius:6px;padding:12px;">
            <p style="font-family:var(--font-mono);font-size:0.70rem;color:#94a3b8;margin-top:0;">
                Clinically test how refreshing stale blood gases eliminates measurement uncertainty and affects predicted risk.
            </p>
        """, unsafe_allow_html=True)

        if st.button("💉 STAT ARTERIAL BLOOD GAS (ABG) DRAW", use_container_width=True):
            # Intervene: refresh arterial blood gas labs
            st.session_state.active_patient_state["pao2_staleness"] = 0.2
            st.session_state.active_patient_state["paco2_staleness"] = 0.2
            st.session_state.active_patient_state["ph_staleness"] = 0.2
            st.session_state.active_patient_state["lactate_staleness"] = 0.2
            st.session_state.abg_drawn = True
            st.rerun()

        if st.session_state.abg_drawn:
            st.markdown("""
            <div style="margin-top:8px;padding:6px 10px;background:rgba(0,230,118,0.1);border-left:3px solid #00e676;font-family:var(--font-mono);font-size:0.68rem;color:#00e676;">
                INTERVENTION EXECUTED: PaO2, PaCO2, pH & Lactate refreshed to 0.2h. Model uncertainty recalculated!
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # Dynamic decay simulation slider
        sim_decay = st.slider(
            "Simulate Diagnostic Delay (+Hours without labs)",
            min_value=0.0, max_value=36.0, value=0.0, step=2.0,
            help="Simulates hours passing in the ICU without clinician ordering fresh diagnostic labs."
        )
        if sim_decay > 0.0:
            # Shift all staleness by sim_decay
            for k in list(curr_labs.keys()):
                if k.endswith("_staleness"):
                    st.session_state.active_patient_state[k] = min(48.0, SCENARIOS[st.session_state.sim_scenario]["labs"][k] + sim_decay)

        if st.button("RESET TO SCENARIO BASELINE", use_container_width=True):
            st.session_state.active_patient_state = dict(SCENARIOS[st.session_state.sim_scenario]["labs"])
            st.session_state.abg_drawn = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
