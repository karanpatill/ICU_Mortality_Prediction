# ventilator_screen.py - High-Fidelity Dual Console: Real Mechanical Ventilator + Bedside Telemetry Monitor
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units
# D. Y. Patil School of Engineering and Management, Kolhapur

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from components.utils import (
    load_model, load_schema, encode_features, load_mimic_10_cohort,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL
)

def build_ventilator_html(p_peak, p_mean, peep, mv, tve, etco2, rr, fio2, patient_id):
    """
    Renders the photorealistic mechanical ventilator console matching user's photo:
    - 3-bar vertical gas flowmeters (yellow, purple, green)
    - 3 synchronized physiological curves: Paw (Yellow), Flow (Green), CO2 (Cyan)
    - Right primary parameters with peak/mean/PEEP, MV/TVexp, EtCO2/Fi, RR/FiO2
    - Touch action keys (Alarm Setup, Auto Limits, System Setup, etc.)
    - Bottom ventilator setpoint strip (Mode VCV, TV, Rate, I:E, PEEP, Pmax)
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            width: 100%;
            height: 100%;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #ffffff;
            user-select: none;
            overflow: hidden;
        }}
        .vent-chassis {{
            background: #eef2f6;
            border: 5px solid #cbd5e1;
            border-radius: 12px;
            padding: 6px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
            height: 350px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .vent-inner-bezel {{
            background: #000000;
            border: 4px solid #1e2430;
            border-radius: 6px;
            padding: 6px 8px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .vent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 4px;
            border-bottom: 1px solid #1f2937;
            font-family: 'JetBrains Mono', monospace;
        }}
        .vent-title {{
            font-size: clamp(0.62rem, 1.0vw, 0.74rem);
            font-weight: 700;
            color: #94a3b8;
            letter-spacing: 0.5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .audio-pause-btn {{
            background: #facc15;
            color: #000000;
            font-weight: 800;
            font-size: clamp(0.52rem, 0.8vw, 0.62rem);
            padding: 2px 8px;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }}
        
        .vent-screen-grid {{
            display: grid;
            grid-template-columns: 22px 1fr minmax(86px, 110px) minmax(56px, 72px);
            gap: 6px;
            flex: 1;
            min-height: 0;
            margin: 4px 0;
        }}
        
        /* Gas flowmeter bars on left */
        .flowmeter-col {{
            display: flex;
            gap: 3px;
            padding-top: 4px;
            height: 100%;
        }}
        .gas-bar {{
            flex: 1;
            background: #111827;
            border: 1px solid #374151;
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 1px;
        }}
        .bar-fill-yellow {{ background: #eab308; height: 48%; border-radius: 1px; }}
        .bar-fill-purple {{ background: #a855f7; height: 62%; border-radius: 1px; }}
        .bar-fill-green  {{ background: #22c55e; height: 54%; border-radius: 1px; }}
        
        .canvas-wrapper {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 0;
            background: #00040a;
            border: 1px solid #1f2937;
            border-radius: 4px;
            overflow: hidden;
        }}
        #ventWaveCanvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: block;
        }}
        
        /* Right primary parameters */
        .vent-params-col {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding-left: 2px;
            overflow: hidden;
        }}
        .param-cell {{
            border-bottom: 1px solid #1e293b;
            padding-bottom: 2px;
        }}
        .param-header {{
            font-size: clamp(0.50rem, 0.78vw, 0.60rem);
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
            white-space: nowrap;
        }}
        .param-big-num {{
            font-size: clamp(1.35rem, 2.1vw, 1.80rem);
            font-weight: 800;
            line-height: 1.05;
            margin: 1px 0;
            font-family: 'JetBrains Mono', monospace;
        }}
        .param-sub-info {{
            font-size: clamp(0.46rem, 0.70vw, 0.56rem);
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
            white-space: nowrap;
        }}
        
        /* Far-right blue buttons */
        .vent-actions-col {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 2px;
        }}
        .v-btn {{
            background: #1e3a8a;
            color: #93c5fd;
            border: 1px solid #3b82f6;
            font-size: clamp(0.42rem, 0.66vw, 0.52rem);
            font-weight: 700;
            padding: 3px 2px;
            text-align: center;
            border-radius: 3px;
            text-transform: uppercase;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .v-btn.end-case {{
            background: #0284c7;
            color: #ffffff;
        }}
        
        /* Bottom ventilator parameter strip */
        .vent-bottom-strip {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 3px 4px;
        }}
        .strip-title {{
            font-size: clamp(0.46rem, 0.68vw, 0.54rem);
            color: #94a3b8;
            text-transform: uppercase;
            margin-bottom: 2px;
            white-space: nowrap;
        }}
        .strip-keys {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 3px;
        }}
        .strip-key {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 3px;
            padding: 2px 2px;
            text-align: center;
            overflow: hidden;
        }}
        .key-label {{
            font-size: clamp(0.42rem, 0.62vw, 0.50rem);
            color: #94a3b8;
            white-space: nowrap;
        }}
        .key-val {{
            font-size: clamp(0.62rem, 0.88vw, 0.76rem);
            font-weight: 800;
            color: #f8fafc;
            white-space: nowrap;
        }}
    </style>
    </head>
    <body>
    <div class="vent-chassis">
        <div class="vent-inner-bezel">
            <div class="vent-header">
                <div class="vent-title">
                    VENTILATOR STATION &bull; {patient_id}
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:clamp(0.62rem, 0.9vw, 0.72rem);font-weight:700;color:#f8fafc;">14:11</span>
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

                <!-- Waveforms Canvas -->
                <div class="canvas-wrapper">
                    <canvas id="ventWaveCanvas"></canvas>
                </div>

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
                    
                    <div style="font-size:clamp(0.48rem, 0.7vw, 0.56rem);color:#94a3b8;display:flex;justify-content:space-between;padding-top:1px;white-space:nowrap;">
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

    <script>
        const canvas = document.getElementById('ventWaveCanvas');
        const ctx = canvas.getContext('2d');
        let cw = 0;
        let ch = 0;
        let sweep = 0;
        let t = 0;

        function resize() {{
            cw = canvas.clientWidth;
            ch = canvas.clientHeight;
            if (cw === 0 || ch === 0) return;
            canvas.width = cw * (window.devicePixelRatio || 1);
            canvas.height = ch * (window.devicePixelRatio || 1);
            ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        }}
        window.addEventListener('resize', resize);
        resize();

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

        function animate() {{
            if (cw === 0 || ch === 0) {{
                resize();
                requestAnimationFrame(animate);
                return;
            }}

            // Phosphor decay trail
            ctx.fillStyle = 'rgba(0, 4, 10, 0.15)';
            ctx.fillRect(0, 0, cw, ch);

            t += 0.016;
            sweep = (sweep + 2.2) % cw;
            ctx.clearRect(sweep, 0, 14, ch);

            const vTime = t * ({rr} / 60) * 0.33;

            // Trace 1: Paw (Yellow) - Top third
            const py = (ch * 0.28) - (pawWave(vTime) * (ch * 0.22));
            ctx.fillStyle = '#facc15';
            ctx.fillRect(sweep, py, 2.5, 2.5);

            // Trace 2: Flow (Green) - Middle third
            const fy = (ch * 0.55) - (flowWave(vTime) * (ch * 0.17));
            ctx.fillStyle = '#22c55e';
            ctx.fillRect(sweep, fy, 2.5, 2.5);

            // Trace 3: CO2 (Cyan) - Bottom third
            const cy = (ch * 0.93) - (co2Wave(vTime) * (ch * 0.22));
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(sweep, cy, 2.5, 2.5);

            // Subtle grid
            ctx.fillStyle = 'rgba(255,255,255,0.02)';
            for (let i = 0; i < ch; i += Math.max(25, ch / 6)) {{
                ctx.fillRect(0, i, cw, 1);
            }}

            requestAnimationFrame(animate);
        }}

        requestAnimationFrame(animate);
    </script>
    </body>
    </html>
    """

def build_telemetry_html(hr, spo2, bp_sys, bp_dia, map_bp, risk_pct):
    """
    Renders the Philips IntelliVue bedside patient monitor:
    - 3 synchronized physiological traces: ECG Lead II (Green), Pleth SpO2 (Cyan), ABP (Rose)
    - Right vitals numerics: HR, SpO2, ABP (sys/dia, MAP)
    - Bottom AURA-ICU AI Copilot Mortality Risk Card with AUROC 0.8559
    """
    risk_color = '#ef4444' if risk_pct >= 70 else ('#f97316' if risk_pct >= 40 else '#10b981')
    risk_label = 'CRITICAL' if risk_pct >= 70 else ('ELEVATED' if risk_pct >= 40 else 'STABLE')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            width: 100%;
            height: 100%;
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #ffffff;
            user-select: none;
            overflow: hidden;
        }}
        .tele-chassis {{
            background: #111827;
            border: 5px solid #1f2937;
            border-radius: 12px;
            padding: 6px 8px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
            height: 350px;
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
            font-family: 'JetBrains Mono', monospace;
        }}
        .tele-title {{
            font-size: clamp(0.62rem, 1.0vw, 0.74rem);
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 0.5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .tele-badge {{
            font-size: clamp(0.55rem, 0.8vw, 0.65rem);
            color: #22c55e;
            font-weight: 700;
            white-space: nowrap;
        }}
        .tele-grid {{
            display: grid;
            grid-template-columns: 1fr minmax(90px, 115px);
            gap: 6px;
            flex: 1;
            min-height: 0;
            margin: 4px 0;
        }}
        .canvas-wrapper {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 0;
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 4px;
            overflow: hidden;
        }}
        #teleWaveCanvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: block;
        }}
        .tele-numerics {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
        }}
        .tele-box {{
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 4px;
            padding: 4px 6px;
        }}
        .t-label {{
            font-size: clamp(0.52rem, 0.8vw, 0.62rem);
            font-weight: 700;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .t-num {{
            font-size: clamp(1.35rem, 2.1vw, 1.80rem);
            font-weight: 800;
            line-height: 1.05;
            margin: 1px 0;
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
        }}
        .t-sub {{
            font-size: clamp(0.46rem, 0.70vw, 0.56rem);
            color: #9ca3af;
            white-space: nowrap;
        }}
        
        .ai-copilot-card {{
            background: linear-gradient(180deg, #0f172a 0%, #030712 100%);
            border: 1px solid #0284c7;
            border-radius: 6px;
            padding: 6px 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .ai-title {{
            font-size: clamp(0.52rem, 0.8vw, 0.62rem);
            color: #94a3b8;
            font-weight: 700;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .ai-risk-val {{
            font-size: clamp(1.0rem, 1.6vw, 1.30rem);
            font-weight: 800;
            line-height: 1.1;
            white-space: nowrap;
        }}
    </style>
    </head>
    <body>
    <div class="tele-chassis">
        <div class="tele-header">
            <div class="tele-title">
                BEDSIDE TELEMETRY &bull; INTELLIVUE
            </div>
            <div class="tele-badge">
                ACTIVE MONITORING
            </div>
        </div>

        <div class="tele-grid">
            <!-- ECG Lead II + Pleth SpO2 + Arterial ABP Traces -->
            <div class="canvas-wrapper">
                <canvas id="teleWaveCanvas"></canvas>
            </div>

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
                    <div class="t-num" style="color:#f43f5e;font-size:clamp(1.05rem, 1.6vw, 1.35rem);margin:2px 0;">{bp_sys}/{bp_dia}</div>
                    <div class="t-sub">MAP: {map_bp} mmHg</div>
                </div>
            </div>
        </div>

        <!-- Integrated AI CDSS Telemetry Card -->
        <div class="ai-copilot-card">
            <div>
                <div class="ai-title">
                    AURA-ICU AI MORTALITY RISK
                </div>
                <div class="ai-risk-val" style="color:{risk_color};">
                    {risk_pct:.1f}% &bull; {risk_label}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:clamp(0.48rem, 0.7vw, 0.56rem);color:#94a3b8;white-space:nowrap;">MODEL AUROC</div>
                <div style="font-size:clamp(0.68rem, 0.95vw, 0.82rem);font-weight:700;color:#22c55e;white-space:nowrap;">0.8559 (p&lt;0.0001)</div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('teleWaveCanvas');
        const ctx = canvas.getContext('2d');
        let cw = 0;
        let ch = 0;
        let sweep = 0;
        let t = 0;

        function resize() {{
            cw = canvas.clientWidth;
            ch = canvas.clientHeight;
            if (cw === 0 || ch === 0) return;
            canvas.width = cw * (window.devicePixelRatio || 1);
            canvas.height = ch * (window.devicePixelRatio || 1);
            ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        }}
        window.addEventListener('resize', resize);
        resize();

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

        function animate() {{
            if (cw === 0 || ch === 0) {{
                resize();
                requestAnimationFrame(animate);
                return;
            }}

            // Phosphor decay clear
            ctx.fillStyle = 'rgba(3, 7, 18, 0.15)';
            ctx.fillRect(0, 0, cw, ch);

            t += 0.016;
            sweep = (sweep + 2.4) % cw;
            ctx.clearRect(sweep, 0, 14, ch);

            const tTime = t * ({hr} / 60) * 1.6;

            // Trace 1: ECG (Green)
            const ey = (ch * 0.24) - (ecgWave(tTime) * (ch * 0.19));
            ctx.fillStyle = '#22c55e';
            ctx.fillRect(sweep, ey, 2.5, 2.5);

            // Trace 2: Pleth (Cyan)
            const ply = (ch * 0.58) - (plethWave(tTime) * (ch * 0.17));
            ctx.fillStyle = '#06b6d4';
            ctx.fillRect(sweep, ply, 2.5, 2.5);

            // Trace 3: ABP (Red)
            const ay = (ch * 0.90) - (abpWave(tTime) * (ch * 0.18));
            ctx.fillStyle = '#f43f5e';
            ctx.fillRect(sweep, ay, 2.5, 2.5);

            requestAnimationFrame(animate);
        }}

        requestAnimationFrame(animate);
    </script>
    </body>
    </html>
    """

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

    # Patient Selector & Display Mode Selector in Responsive Columns
    c_pat, c_view = st.columns([1.6, 1.4])
    with c_pat:
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

    with c_view:
        view_mode = st.radio(
            "Workstation Console Display Mode",
            ["Dual Workstation (Side-by-Side)", "Ventilator Focus (Wide)", "Bedside Telemetry Focus (Wide)"],
            horizontal=True
        )

    active_p = patients[st.session_state.vent_patient_idx]
    is_crit = (active_p["outcome_death"] == 1)

    # Derive authentic ventilator parameters matching user's photo
    p_peak = 28 if is_crit else 19
    p_mean = 11 if is_crit else 7
    peep = 8 if is_crit else 2
    mv = 9.4 if is_crit else 7.6
    tve = 480 if is_crit else 545
    etco2 = 38 if is_crit else 26
    rr = 20 if is_crit else 14
    fio2 = 70 if is_crit else 51

    # Derive authentic patient hemodynamics
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

    # Pre-render HTML code for both screens
    vent_html = build_ventilator_html(
        p_peak=p_peak, p_mean=p_mean, peep=peep, mv=mv, tve=tve, etco2=etco2, rr=rr, fio2=fio2,
        patient_id=active_p["clinical_case_id"]
    )
    tele_html = build_telemetry_html(
        hr=hr, spo2=spo2, bp_sys=bp_sys, bp_dia=bp_dia, map_bp=map_bp, risk_pct=predicted_risk_pct
    )

    # Responsive Render Based on User View Choice
    if view_mode == "Dual Workstation (Side-by-Side)":
        col_vent, col_tele = st.columns([1.18, 0.82], gap="small")
        with col_vent:
            components.html(vent_html, height=365, scrolling=False)
        with col_tele:
            components.html(tele_html, height=365, scrolling=False)
    elif view_mode == "Ventilator Focus (Wide)":
        components.html(vent_html, height=365, scrolling=False)
    else:
        components.html(tele_html, height=365, scrolling=False)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Clean Responsive Metrics Row
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
