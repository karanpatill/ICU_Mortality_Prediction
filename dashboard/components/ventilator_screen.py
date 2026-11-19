# ventilator_screen.py - High-Fidelity Dual Console: Real Mechanical Ventilator + Bedside Telemetry Monitor
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units
# D. Y. Patil School of Engineering and Management, Kolhapur

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json
from components.utils import (
    load_model, load_schema, encode_features, load_mimic_10_cohort,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL, SENTINEL_HOURS
)

def render_dual_icu_screens(
    p_peak=19, p_mean=7, peep=2, mv=7.6, tve=545, etco2=26, rr=14, fio2=51,
    hr=82, spo2=98, bp_sys=120, bp_dia=78, map_bp=92, risk_pct=34.2, patient_id="MIMIC-PT-01"
):
    """
    Renders TWO authentic medical consoles side-by-side:
    1. LEFT CONSOLE: GE Datex-Ohmeda / Mindray Anesthesia & Mechanical Ventilator
       (Matching user's photo with 3 waveforms: Paw, Flow, CO2 + Gas bars + Param keys)
    2. RIGHT CONSOLE: Philips IntelliVue / Mindray Multiparameter Patient Bedside Monitor
       (ECG Lead II, Pleth SpO2, Invasive Arterial ABP + AURA-ICU Neural AI Engine)
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #090e17;
            font-family: -apple-system, 'Segoe UI', 'JetBrains Mono', monospace;
            color: #ffffff;
            user-select: none;
            overflow: hidden;
            padding: 8px;
        }}
        .console-container {{
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 14px;
            width: 100%;
        }}
        
        /* ─── 1. REAL VENTILATOR CONSOLE (MATCHING USER PHOTO) ─── */
        .vent-chassis {{
            background: #eef2f6;
            border: 8px solid #d8e2ec;
            border-radius: 14px;
            padding: 6px;
            box-shadow: 0 16px 36px rgba(0,0,0,0.6);
        }}
        .vent-inner-bezel {{
            background: #000000;
            border: 5px solid #1e2430;
            border-radius: 6px;
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .vent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 4px;
            border-bottom: 1px solid #222b3a;
        }}
        .audio-pause-btn {{
            background: #facc15;
            color: #000000;
            font-weight: 800;
            font-size: 0.70rem;
            padding: 3px 10px;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .vent-screen-grid {{
            display: grid;
            grid-template-columns: 36px 1fr 115px 78px;
            gap: 6px;
            height: 290px;
        }}
        
        /* Gas flowmeter bars on left */
        .flowmeter-col {{
            display: flex;
            gap: 3px;
            padding-top: 10px;
        }}
        .gas-bar {{
            flex: 1;
            background: #111827;
            border: 1px solid #374151;
            border-radius: 2px;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 1px;
        }}
        .bar-fill-yellow {{ background: #eab308; height: 45%; border-radius: 1px; }}
        .bar-fill-purple {{ background: #a855f7; height: 60%; border-radius: 1px; }}
        .bar-fill-green  {{ background: #22c55e; height: 52%; border-radius: 1px; }}
        
        #ventWaveCanvas {{
            width: 100%;
            height: 100%;
            background: #00040a;
            border: 1px solid #1f2937;
            border-radius: 4px;
            display: block;
        }}
        
        /* Right primary parameters */
        .vent-params-col {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding-left: 2px;
        }}
        .param-cell {{
            border-bottom: 1px solid #1e293b;
            padding-bottom: 4px;
        }}
        .param-header {{
            font-size: 0.60rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }}
        .param-big-num {{
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1;
            margin: 2px 0;
            letter-spacing: -1px;
        }}
        .param-sub-info {{
            font-size: 0.58rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }}
        
        /* Far-right blue buttons */
        .vent-actions-col {{
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}
        .v-btn {{
            background: #1e3a8a;
            color: #93c5fd;
            border: 1px solid #3b82f6;
            font-size: 0.55rem;
            font-weight: 700;
            padding: 4px 2px;
            text-align: center;
            border-radius: 3px;
            text-transform: uppercase;
        }}
        .v-btn.end-case {{
            background: #0284c7;
            color: #ffffff;
            margin-top: auto;
        }}
        
        /* Bottom ventilator parameter strip */
        .vent-bottom-strip {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 4px 6px;
        }}
        .strip-title {{
            font-size: 0.58rem;
            color: #94a3b8;
            text-transform: uppercase;
            margin-bottom: 3px;
        }}
        .strip-keys {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
        }}
        .strip-key {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 3px;
            padding: 3px 4px;
            text-align: center;
        }}
        .key-label {{ font-size: 0.52rem; color: #94a3b8; }}
        .key-val {{ font-size: 0.75rem; font-weight: 800; color: #f8fafc; }}

        /* ─── 2. REAL PATIENT BEDSIDE TELEMETRY MONITOR (PHILIPS STYLE) ─── */
        .tele-chassis {{
            background: #111827;
            border: 6px solid #1f2937;
            border-radius: 14px;
            padding: 8px;
            box-shadow: 0 16px 36px rgba(0,0,0,0.6);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .tele-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #374151;
            padding-bottom: 4px;
            margin-bottom: 6px;
        }}
        .tele-grid {{
            display: grid;
            grid-template-columns: 1fr 105px;
            gap: 8px;
            height: 290px;
        }}
        #teleWaveCanvas {{
            width: 100%;
            height: 100%;
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 4px;
            display: block;
        }}
        .tele-numerics {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .tele-box {{
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 4px;
            padding: 5px 8px;
        }}
        .t-label {{ font-size: 0.60rem; font-weight: 700; text-transform: uppercase; }}
        .t-num {{ font-size: 2.0rem; font-weight: 800; line-height: 1; margin: 2px 0; }}
        .t-sub {{ font-size: 0.55rem; color: #9ca3af; }}
        
        .ai-copilot-card {{
            background: linear-gradient(180deg, #0f172a 0%, #030712 100%);
            border: 1px solid #0284c7;
            border-radius: 6px;
            padding: 8px 12px;
            margin-top: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
    </style>
    </head>
    <body>
    <div class="console-container">
        
        <!-- 1. REAL VENTILATOR WORKSTATION -->
        <div class="vent-chassis">
            <div class="vent-inner-bezel">
                <div class="vent-header">
                    <div style="font-size:0.75rem;font-weight:700;color:#94a3b8;letter-spacing:1px;">
                        VENTILATOR STATION &bull; {patient_id}
                    </div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:0.75rem;font-weight:700;color:#f8fafc;">14:11</span>
                        <span class="audio-pause-btn">Audio Pause</span>
                    </div>
                </div>

                <div class="vent-screen-grid">
                    <!-- Flowmeter Bar Columns -->
                    <div class="flowmeter-col">
                        <div class="gas-bar"><div class="bar-fill-yellow"></div></div>
                        <div class="gas-bar"><div class="bar-fill-purple"></div></div>
                        <div class="gas-bar"><div class="bar-fill-green"></div></div>
                    </div>

                    <!-- 3 Real Mechanical Waveforms (Paw, Flow, CO2) -->
                    <canvas id="ventWaveCanvas"></canvas>

                    <!-- Telemetry Numeric Columns -->
                    <div class="vent-params-col">
                        <div class="param-cell">
                            <div class="param-header"><span style="color:#facc15;">Paw cmH2O</span><span>40</span></div>
                            <div class="param-big-num" style="color:#facc15;">{p_peak}</div>
                            <div class="param-sub-info"><span>Pmean {p_mean}</span><span>PEEP {peep}</span></div>
                        </div>

                        <div class="param-cell">
                            <div class="param-header"><span style="color:#22c55e;">Flow l/min</span><span>2.0/10.0</span></div>
                            <div class="param-big-num" style="color:#22c55e;">{mv}</div>
                            <div class="param-sub-info"><span>TVexp ml</span><span>{tve}</span></div>
                        </div>

                        <div class="param-cell" style="border:none;">
                            <div class="param-header"><span style="color:#38bdf8;">CO2 mmHg</span><span>25/50</span></div>
                            <div class="param-big-num" style="color:#38bdf8;">{etco2}</div>
                            <div class="param-sub-info"><span>Fi</span><span>1</span></div>
                        </div>
                        
                        <div style="font-size:0.55rem;color:#94a3b8;display:flex;justify-content:space-between;padding-top:2px;">
                            <span>RR: {rr}</span>
                            <span>FiO2: {fio2}%</span>
                        </div>
                    </div>

                    <!-- Vertical Menu Action Buttons -->
                    <div class="vent-actions-col">
                        <div class="v-btn">Alarm Setup</div>
                        <div class="v-btn">Auto Limits</div>
                        <div class="v-btn">System Setup</div>
                        <div class="v-btn">Next Page</div>
                        <div class="v-btn">Trends</div>
                        <div class="v-btn">Spirometry</div>
                        <div class="v-btn">Procedures</div>
                        <div class="v-btn end-case">End Case</div>
                    </div>
                </div>

                <!-- Bottom Ventilator Setpoints Strip -->
                <div class="vent-bottom-strip">
                    <div class="strip-title">Ventilator On | Volume Control</div>
                    <div class="strip-keys">
                        <div class="strip-key"><div class="key-label">Mode</div><div class="key-val">VCV</div></div>
                        <div class="strip-key"><div class="key-label">TV (ml)</div><div class="key-val">{tve}</div></div>
                        <div class="strip-key"><div class="key-label">Rate</div><div class="key-val">{rr}</div></div>
                        <div class="strip-key"><div class="key-label">I:E</div><div class="key-val">1:2</div></div>
                        <div class="strip-key"><div class="key-label">Tpause</div><div class="key-val">Off</div></div>
                        <div class="strip-key"><div class="key-label">PEEP</div><div class="key-val">{peep}</div></div>
                        <div class="strip-key"><div class="key-label">Pmax</div><div class="key-val">40</div></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2. REAL MULTIPARAMETER PATIENT BEDSIDE MONITOR -->
        <div class="tele-chassis">
            <div>
                <div class="tele-header">
                    <div style="font-size:0.75rem;font-weight:700;color:#38bdf8;letter-spacing:1px;">
                        PATIENT BEDSIDE TELEMETRY &bull; INTELLIVUE
                    </div>
                    <div style="font-size:0.70rem;color:#22c55e;font-weight:700;">
                        ACTIVE MONITORING
                    </div>
                </div>

                <div class="tele-grid">
                    <!-- ECG Lead II + Pleth SpO2 + Arterial ABP Traces -->
                    <canvas id="teleWaveCanvas"></canvas>

                    <!-- Vitals Digitals -->
                    <div class="tele-numerics">
                        <div class="tele-box" style="border-left:3px solid #22c55e;">
                            <div class="t-label" style="color:#22c55e;">HR bpm</div>
                            <div class="t-num" style="color:#22c55e;">{hr}</div>
                            <div class="t-sub">ST II: -0.2 mm</div>
                        </div>

                        <div class="tele-box" style="border-left:3px solid #06b6d4;">
                            <div class="t-label" style="color:#06b6d4;">SpO2 %</div>
                            <div class="t-num" style="color:#06b6d4;">{spo2}</div>
                            <div class="t-sub">PI: 4.8 %</div>
                        </div>

                        <div class="tele-box" style="border-left:3px solid #f43f5e;">
                            <div class="t-label" style="color:#f43f5e;">ABP mmHg</div>
                            <div class="t-num" style="color:#f43f5e;font-size:1.4rem;margin:5px 0;">{bp_sys}/{bp_dia}</div>
                            <div class="t-sub">MAP: {map_bp} mmHg</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Integrated AI CDSS Telemetry Card -->
            <div class="ai-copilot-card">
                <div>
                    <div style="font-size:0.65rem;color:#94a3b8;font-weight:700;text-transform:uppercase;">
                        AURA-ICU AI MORTALITY RISK
                    </div>
                    <div style="font-size:1.35rem;font-weight:800;color:{'#ef4444' if risk_pct >= 70 else ('#f97316' if risk_pct >= 40 else '#10b981')};">
                        {risk_pct:.1f}% &bull; {'CRITICAL' if risk_pct >= 70 else ('ELEVATED' if risk_pct >= 40 else 'STABLE')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.60rem;color:#94a3b8;">MODEL AUROC</div>
                    <div style="font-size:0.80rem;font-weight:700;color:#22c55e;">0.8559 (p&lt;0.0001)</div>
                </div>
            </div>
        </div>

    </div>

    <!-- 60 FPS SYNCHRONIZED WAVEFORM GENERATION ENGINE -->
    <script>
        // Setup Canvas 1: Ventilator (Paw, Flow, CO2)
        const vCanvas = document.getElementById('ventWaveCanvas');
        const vCtx = vCanvas.getContext('2d');
        vCanvas.width = vCanvas.clientWidth * window.devicePixelRatio;
        vCanvas.height = vCanvas.clientHeight * window.devicePixelRatio;
        vCtx.scale(window.devicePixelRatio, window.devicePixelRatio);

        // Setup Canvas 2: Telemetry (ECG, Pleth, ABP)
        const tCanvas = document.getElementById('teleWaveCanvas');
        const tCtx = tCanvas.getContext('2d');
        tCanvas.width = tCanvas.clientWidth * window.devicePixelRatio;
        tCanvas.height = tCanvas.clientHeight * window.devicePixelRatio;
        tCtx.scale(window.devicePixelRatio, window.devicePixelRatio);

        let sweepV = 0;
        let sweepT = 0;
        let t = 0;

        function pawWave(p) {{
            const ph = p % 1.0;
            if (ph < 0.33) return Math.sin(ph / 0.33 * Math.PI * 0.5);
            return Math.exp(-(ph - 0.33) * 6.5);
        }}

        function flowWave(p) {{
            const ph = p % 1.0;
            if (ph < 0.33) return (1.0 - (ph / 0.33)) * 0.95;
            return -Math.exp(-(ph - 0.33) * 7.5) * 0.9;
        }}

        function co2Wave(p) {{
            const ph = p % 1.0;
            if (ph < 0.1) return (ph / 0.1);
            if (ph < 0.4) return 0.95 + Math.sin((ph - 0.1)/0.3 * Math.PI) * 0.05;
            if (ph < 0.48) return (1.0 - ((ph - 0.4) / 0.08));
            return 0.0;
        }}

        function ecgWave(p) {{
            const ph = p % 1.0;
            if (ph > 0.15 && ph < 0.22) return Math.sin((ph - 0.15) / 0.07 * Math.PI) * 0.18;
            if (ph > 0.32 && ph < 0.34) return -0.15;
            if (ph >= 0.34 && ph < 0.38) return 1.0;
            if (ph >= 0.38 && ph < 0.41) return -0.35;
            if (ph > 0.48 && ph < 0.65) return Math.sin((ph - 0.48) / 0.17 * Math.PI) * 0.28;
            return 0.0;
        }}

        function plethWave(p) {{
            const ph = p % 1.0;
            if (ph < 0.25) return Math.sin(ph / 0.25 * Math.PI * 0.5);
            if (ph < 0.4) return Math.cos((ph - 0.25) / 0.15 * Math.PI * 0.5) * 0.4 + 0.6;
            return Math.exp(-(ph - 0.4) * 4) * 0.6;
        }}

        function abpWave(p) {{
            const ph = p % 1.0;
            if (ph < 0.18) return Math.sin(ph / 0.18 * Math.PI * 0.5);
            if (ph < 0.35) return Math.cos((ph - 0.18) / 0.17 * Math.PI * 0.5) * 0.35 + 0.65;
            return Math.exp(-(ph - 0.35) * 5) * 0.65;
        }}

        function loop() {{
            const vW = vCanvas.clientWidth;
            const vH = vCanvas.clientHeight;
            const tW = tCanvas.clientWidth;
            const tH = tCanvas.clientHeight;

            // Phosphorus decay clear
            vCtx.fillStyle = 'rgba(0, 4, 10, 0.15)';
            vCtx.fillRect(0, 0, vW, vH);

            tCtx.fillStyle = 'rgba(3, 7, 18, 0.15)';
            tCtx.fillRect(0, 0, tW, tH);

            t += 0.016;

            // 1. Draw Ventilator Screen (Sweep V)
            sweepV = (sweepV + 2.2) % vW;
            vCtx.clearRect(sweepV, 0, 14, vH);

            const vTime = t * ({rr} / 60) * 0.33;
            // Trace 1: Paw (Yellow)
            const py = 80 - (pawWave(vTime) * 60);
            vCtx.fillStyle = '#facc15';
            vCtx.fillRect(sweepV, py, 2.5, 2.5);

            // Trace 2: Flow (Green)
            const fy = 165 - (flowWave(vTime) * 45);
            vCtx.fillStyle = '#22c55e';
            vCtx.fillRect(sweepV, fy, 2.5, 2.5);

            // Trace 3: CO2 (Cyan)
            const cy = 265 - (co2Wave(vTime) * 55);
            vCtx.fillStyle = '#38bdf8';
            vCtx.fillRect(sweepV, cy, 2.5, 2.5);

            // 2. Draw Patient Monitor Screen (Sweep T)
            sweepT = (sweepT + 2.4) % tW;
            tCtx.clearRect(sweepT, 0, 14, tH);

            const tTime = t * ({hr} / 60) * 1.6;
            // Trace 1: ECG (Green)
            const ey = 45 - (ecgWave(tTime) * 32);
            tCtx.fillStyle = '#22c55e';
            tCtx.fillRect(sweepT, ey, 2.5, 2.5);

            // Trace 2: Pleth (Cyan)
            const ply = 135 - (plethWave(tTime) * 30);
            tCtx.fillStyle = '#06b6d4';
            tCtx.fillRect(sweepT, ply, 2.5, 2.5);

            // Trace 3: ABP (Red)
            const ay = 230 - (abpWave(tTime) * 35);
            tCtx.fillStyle = '#f43f5e';
            tCtx.fillRect(sweepT, ay, 2.5, 2.5);

            // Grid lines on ventilator
            vCtx.fillStyle = 'rgba(255,255,255,0.02)';
            for (let i = 0; i < vH; i += 40) vCtx.fillRect(0, i, vW, 1);

            requestAnimationFrame(loop);
        }}

        loop();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=420, scrolling=False)


def render_ventilator_screen():
    model = load_model()
    schema = load_schema()
    patients = load_mimic_10_cohort()

    if "vent_patient_idx" not in st.session_state:
        st.session_state.vent_patient_idx = 0
    if "vent_delay_hours" not in st.session_state:
        st.session_state.vent_delay_hours = 0.0
    if "vent_abg_active" not in st.session_state:
        st.session_state.vent_abg_active = False

    st.markdown("### Clinical Dual-Console: ICU Mechanical Ventilator & Bedside Telemetry Monitor")
    st.caption("Synchronized Real-Time Workstation Display | Targeted Laboratory Staleness Surveillance")

    # Inpatient Selection Selector
    patient_opts = [
        f"{p['clinical_case_id']} — Stay #{p['stay_id']} ({p['gender']}, {p['age']}y) | {p['first_careunit']}"
        for p in patients
    ]
    sel_opt = st.selectbox(
        "Select Active Inpatient Profile",
        patient_opts,
        index=st.session_state.vent_patient_idx
    )
    new_idx = patient_opts.index(sel_opt)
    if new_idx != st.session_state.vent_patient_idx:
        st.session_state.vent_patient_idx = new_idx
        st.session_state.vent_delay_hours = 0.0
        st.session_state.vent_abg_active = False
        st.rerun()

    active_p = patients[st.session_state.vent_patient_idx]
    is_crit = (active_p["outcome_death"] == 1)

    # 1. Derive authentic ventilator parameters matching user's photo
    p_peak = 28 if is_crit else 19
    p_mean = 11 if is_crit else 7
    peep = 8 if is_crit else 2
    mv = 9.4 if is_crit else 7.6
    tve = 480 if is_crit else 545
    etco2 = 38 if is_crit else 26
    rr = 20 if is_crit else 14
    fio2 = 70 if is_crit else 51

    # 2. Derive authentic patient hemodynamics
    hr = 112 if is_crit else 82
    spo2 = 92 if is_crit else 98
    bp_sys = 94 if is_crit else 120
    bp_dia = 58 if is_crit else 78
    map_bp = int((bp_sys + 2 * bp_dia) / 3)

    # Calculate AI Model Prediction with Delay
    p_copy = dict(active_p)
    delay = st.session_state.vent_delay_hours

    for lab in LAB_NAMES:
        col_s = f"{lab}_staleness"
        base_s = float(p_copy.get(col_s, 48.0))
        p_copy[col_s] = min(48.0, base_s + delay)

    if st.session_state.vent_abg_active:
        p_copy["pao2_staleness"] = 0.2
        p_copy["paco2_staleness"] = 0.2
        p_copy["ph_staleness"] = 0.2
        p_copy["lactate_staleness"] = 0.2

    X_in = encode_features(pd.DataFrame([p_copy]), schema["features"])
    predicted_risk_pct = float(model.predict_proba(X_in)[:, 1][0] * 100.0)
    actual_outcome = "EXPIRED" if active_p["outcome_death"] == 1 else "SURVIVED"

    # Render Dual Screen Component
    render_dual_icu_screens(
        p_peak=p_peak, p_mean=p_mean, peep=peep, mv=mv, tve=tve, etco2=etco2, rr=rr, fio2=fio2,
        hr=hr, spo2=spo2, bp_sys=bp_sys, bp_dia=bp_dia, map_bp=map_bp, risk_pct=predicted_risk_pct,
        patient_id=active_p["clinical_case_id"]
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AI Predicted Mortality Risk", f"{predicted_risk_pct:.1f}%")
    m2.metric("MIMIC-IV Ground Truth", actual_outcome)
    m3.metric("Care Unit", active_p["first_careunit"])
    m4.metric("Ventilator Elapsed", f"{int(active_p['vent_duration_hours'])} Hours")

    st.divider()

    # Interactive Bedside Actions & Dynamic Aging
    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("#### Bedside Diagnostic Interventions")
        st.caption("Evaluate how refreshing stale arterial blood gases impacts model uncertainty in real time.")
        
        if st.button("EXECUTE STAT ARTERIAL BLOOD GAS (ABG) DRAW", use_container_width=True):
            st.session_state.vent_abg_active = True
            st.rerun()

        if st.session_state.vent_abg_active:
            st.success("INTERVENTION EXECUTED: PaO2, PaCO2, pH & Lactate staleness refreshed to 0.2h.")

        if st.button("Reset Inpatient State", use_container_width=True):
            st.session_state.vent_delay_hours = 0.0
            st.session_state.vent_abg_active = False
            st.rerun()

    with col_act2:
        st.markdown("#### Diagnostic Delay Simulation")
        st.caption("Simulate clinical hours passing without lab testing to watch staleness decay elevate risk.")
        
        delay_val = st.slider(
            "Diagnostic Delay (+Hours without lab redraw)",
            0.0, 36.0, float(st.session_state.vent_delay_hours), 2.0
        )
        if delay_val != st.session_state.vent_delay_hours:
            st.session_state.vent_delay_hours = delay_val
            st.rerun()

    st.markdown("#### Active Biomarkers & Observation Recency")
    table_data = []
    for lab in LAB_NAMES:
        val = p_copy.get(f"{lab}_val", np.nan)
        h = p_copy.get(f"{lab}_staleness", 48.0)
        table_data.append({
            "Biomarker": LAB_DISPLAY[lab],
            "Measured Value": f"{val:.2f} {LAB_UNITS[lab]}" if not np.isnan(val) else "Not Drawn",
            "Reference Interval": f"{LAB_NORMAL[lab][0]} - {LAB_NORMAL[lab][1]} {LAB_UNITS[lab]}",
            "Observation Age": f"{h:.1f} Hours",
            "Staleness Status": "STALE (>20h)" if h >= 20.0 else ("MODERATE (6-20h)" if h >= 6.0 else "FRESH (<6h)")
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
