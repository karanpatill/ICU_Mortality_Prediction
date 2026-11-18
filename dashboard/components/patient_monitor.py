# patient_monitor.py - Clinical Diagnostic Deep-Dive Console
# AURA-ICU: Adaptive Uncertainty-aware Risk Assessment for Intensive Care Units

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from components.utils import (
    load_model, load_schema, classify_risk, classify_staleness,
    get_staleness_summary, get_feature_importance, get_ward_patients,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL, SENTINEL_HOURS
)

def render_risk_gauge(risk_pct: float):
    """Render high-precision medical telemetry risk gauge."""
    risk_cls = classify_risk(risk_pct)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_pct,
        number=dict(
            suffix="%",
            font=dict(color=risk_cls["color"], size=46, family="Chakra Petch, JetBrains Mono"),
            valueformat=".1f"
        ),
        delta=dict(
            reference=17.2,
            relative=False,
            increasing=dict(color="#ff1744"),
            decreasing=dict(color="#00e676"),
            valueformat=".1f",
            suffix="% vs baseline"
        ),
        title=dict(
            text=f"<b style='font-family:JetBrains Mono;letter-spacing:2px;'>MORTALITY RISK</b><br><span style='font-size:0.75em;color:#718096;font-family:JetBrains Mono;'>{risk_cls['label']}</span>",
            font=dict(color="#edf2f7", size=14)
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor="#25374f",
                tickfont=dict(color="#718096", size=10, family="JetBrains Mono"),
                tickvals=[0, 17, 25, 50, 70, 100],
                ticktext=["0%", "Avg", "25%", "50%", "70%", "100%"]
            ),
            bar=dict(color=risk_cls["color"], thickness=0.25),
            bgcolor="#080d14",
            borderwidth=1,
            bordercolor="#1c2738",
            steps=[
                dict(range=[0, 25], color="rgba(0, 230, 118, 0.08)"),
                dict(range=[25, 50], color="rgba(255, 214, 0, 0.08)"),
                dict(range=[50, 70], color="rgba(255, 145, 0, 0.08)"),
                dict(range=[70, 100], color="rgba(255, 23, 68, 0.08)"),
            ],
            threshold=dict(
                line=dict(color="#00e5ff", width=2),
                thickness=0.85,
                value=17.2
            ),
        )
    ))
    fig.update_layout(
        paper_bgcolor="#090e15",
        plot_bgcolor="#090e15",
        font=dict(color="#edf2f7"),
        height=280,
        margin=dict(t=35, b=15, l=25, r=25),
    )
    return fig

def render_staleness_trajectory_chart(patient_row: pd.Series):
    """
    Simulates a 24-hour retrospective risk trajectory showing how
    staleness accumulation increases uncertainty over time.
    """
    hours = np.linspace(-24, 0, 25)
    base_risk = float(patient_row.get("risk_pct", 35.0))
    
    # Synthetic realistic decay path ending at current risk
    trajectory = []
    current = max(5.0, base_risk - 15.0)
    for h in hours:
        if h == -12:
            current -= 4.0  # sudden lab redraw dip
        else:
            current += np.random.uniform(0.2, 1.2)
        trajectory.append(min(98.0, max(2.0, current)))
    trajectory[-1] = base_risk

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=trajectory,
        mode="lines+markers",
        line=dict(color="#00e5ff", width=2.5),
        marker=dict(size=4, color="#00e5ff"),
        fill="tozeroy",
        fillcolor="rgba(0, 229, 255, 0.06)",
        name="Risk Trajectory"
    ))
    
    # Critical threshold line
    fig.add_hline(y=70, line_dash="dash", line_color="#ff1744", line_width=1,
                  annotation_text="CRITICAL THRESHOLD (70%)", annotation_font_size=9,
                  annotation_font_color="#ff1744", annotation_position="top left")
    
    fig.add_hline(y=17.2, line_dash="dot", line_color="#718096", line_width=1,
                  annotation_text="ICU AVERAGE (17.2%)", annotation_font_size=9,
                  annotation_font_color="#718096", annotation_position="bottom left")

    fig.update_layout(
        title=dict(
            text="24-HOUR DYNAMIC MORTALITY RISK TRAJECTORY",
            font=dict(color="#edf2f7", size=11, family="JetBrains Mono"),
            x=0
        ),
        paper_bgcolor="#090e15",
        plot_bgcolor="#090e15",
        font=dict(color="#edf2f7", size=10, family="JetBrains Mono"),
        xaxis=dict(
            title="Hours Preceding Current Evaluation (h)",
            gridcolor="#142030",
            tickfont=dict(color="#718096"),
            titlefont=dict(color="#718096", size=9)
        ),
        yaxis=dict(
            title="Predicted Mortality (%)",
            range=[0, 100],
            gridcolor="#142030",
            tickfont=dict(color="#718096"),
            titlefont=dict(color="#718096", size=9)
        ),
        height=280,
        margin=dict(t=40, b=35, l=45, r=15)
    )
    return fig

def render_patient_monitor():
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=12)

    # Patient Selector
    st.markdown("""
    <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">
        SELECT INPATIENT TELEMETRY STREAM
    </div>
    """, unsafe_allow_html=True)

    bed_options = [
        f"{row['bed_id']} | Risk: {row['risk_pct']:.1f}% | Age: {int(row['age'])}y | {str(row['first_careunit'])[:28]}"
        for _, row in ward_df.iterrows()
    ]
    default_idx = st.session_state.get("selected_bed_idx", 0)
    selected_opt = st.selectbox("Choose Patient Bed", bed_options, index=default_idx, label_visibility="collapsed")
    sel_idx = int(selected_opt.split("|")[0].replace("BED-", "").strip()) - 1
    patient = ward_df.iloc[sel_idx]
    st.session_state.selected_bed_idx = sel_idx

    risk_pct = float(patient["risk_pct"])
    risk_cls = classify_risk(risk_pct)
    gender_txt = "Male" if patient.get("gender") == "M" else "Female"
    age = int(patient.get("age", 0))
    unit = str(patient.get("first_careunit", "ICU"))
    vent_h = int(patient.get("vent_duration_hours", 0))

    # Top Inpatient Banner
    st.markdown(f"""
    <div style="background:#090e15;border:1px solid #1c2738;border-left:4px solid {risk_cls['color']};border-radius:6px;padding:12px 18px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
        <div>
            <div style="font-family:var(--font-display);font-size:1.25rem;font-weight:700;color:#edf2f7;letter-spacing:1px;">
                BED {patient['bed_id']} &bull; PATIENT ADMISSION ID: #{patient['hadm_id']}
            </div>
            <div style="font-family:var(--font-mono);font-size:0.72rem;color:#718096;margin-top:2px;">
                {gender_txt}, {age} Years &bull; Unit: {unit} &bull; Invasive Mechanical Ventilation: {vent_h} Hours
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">CLINICAL STATUS</div>
            <div style="font-family:var(--font-mono);font-size:0.85rem;font-weight:700;color:{risk_cls['color']};">
                {risk_cls['label']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Row: Gauge & 24h Trajectory Chart
    col_gauge, col_traj = st.columns([1.1, 1.9])
    with col_gauge:
        fig_g = render_risk_gauge(risk_pct)
        st.plotly_chart(fig_g, use_container_width=True, key="mon_gauge")

    with col_traj:
        fig_traj = render_staleness_trajectory_chart(patient)
        st.plotly_chart(fig_traj, use_container_width=True, key="mon_traj")

    # Bottom Row: Comprehensive Lab Panel
    st.markdown("""
    <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:1.5px;text-transform:uppercase;margin:16px 0 8px 0;">
        ACTIVE 13-BIOMARKER STALENESS & MEASUREMENT AUDIT
    </div>
    """, unsafe_allow_html=True)

    stale_summary = get_staleness_summary(patient)
    table_rows = ""
    for lab, data in stale_summary.items():
        v = data["value"]
        lo, hi = data["normal"]
        cls = data["classification"]
        h = data["hours"]

        val_str = f"{v:.2f} {data['unit']}" if not np.isnan(v) else "NOT DRAWN"
        status_txt = "NORMAL"
        val_color = "#edf2f7"
        if not np.isnan(v):
            if v < lo:
                status_txt = "LOW"
                val_color = "#00e5ff"
            elif v > hi:
                status_txt = "HIGH"
                val_color = "#ff1744"

        h_str = f"{h:.1f} Hours" if h < SENTINEL_HOURS else "≥ 48.0 Hours (SENTINEL)"
        table_rows += f"""
        <tr style="border-bottom:1px solid #142030;font-family:var(--font-mono);font-size:0.74rem;">
            <td style="padding:7px 12px;color:#edf2f7;font-weight:600;">{data['display']}</td>
            <td style="padding:7px 12px;color:{val_color};font-weight:700;">{val_str}</td>
            <td style="padding:7px 12px;color:#718096;">{lo} – {hi} {data['unit']}</td>
            <td style="padding:7px 12px;color:#edf2f7;">{h_str}</td>
            <td style="padding:7px 12px;text-align:right;">
                <span style="color:{cls['color']};background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:2px;font-size:0.65rem;font-weight:700;border:1px solid {cls['color']}44;">
                    {cls['label'].upper()}
                </span>
            </td>
        </tr>
        """

    st.markdown(f"""
    <div style="background:#090e15;border:1px solid #1c2738;border-radius:6px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;text-align:left;">
            <thead>
                <tr style="background:#0d141e;border-bottom:1px solid #1c2738;font-family:var(--font-mono);font-size:0.65rem;color:#718096;text-transform:uppercase;">
                    <th style="padding:8px 12px;">Biomarker</th>
                    <th style="padding:8px 12px;">Current Value</th>
                    <th style="padding:8px 12px;">Reference Interval</th>
                    <th style="padding:8px 12px;">Sampling Age</th>
                    <th style="padding:8px 12px;text-align:right;">Staleness Classification</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
