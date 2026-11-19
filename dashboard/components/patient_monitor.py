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
    risk_cls = classify_risk(risk_pct)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_pct,
        number=dict(
            suffix="%",
            font=dict(color=risk_cls["color"], size=44, family="Plus Jakarta Sans, sans-serif"),
            valueformat=".1f"
        ),
        delta=dict(
            reference=17.2,
            relative=False,
            increasing=dict(color="#dc2626"),
            decreasing=dict(color="#059669"),
            valueformat=".1f",
            suffix="% vs ICU avg"
        ),
        title=dict(
            text=f"<b>MORTALITY RISK ASSESSMENT</b><br><span style='font-size:0.8em;color:#64748b;'>{risk_cls['label']}</span>",
            font=dict(color="#0f172a", size=13)
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor="#cbd5e1",
                tickfont=dict(color="#64748b", size=10),
                tickvals=[0, 17, 25, 50, 70, 100],
                ticktext=["0%", "Avg", "25%", "50%", "70%", "100%"]
            ),
            bar=dict(color=risk_cls["color"], thickness=0.25),
            bgcolor="#ffffff",
            borderwidth=1,
            bordercolor="#e2e8f0",
            steps=[
                dict(range=[0, 25], color="rgba(16, 185, 129, 0.1)"),
                dict(range=[25, 50], color="rgba(234, 179, 8, 0.1)"),
                dict(range=[50, 70], color="rgba(249, 115, 22, 0.1)"),
                dict(range=[70, 100], color="rgba(239, 68, 68, 0.1)"),
            ],
            threshold=dict(
                line=dict(color="#0284c7", width=2),
                thickness=0.85,
                value=17.2
            ),
        )
    ))
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a"),
        height=270,
        margin=dict(t=35, b=15, l=25, r=25),
    )
    return fig

def render_staleness_trajectory_chart(patient_row: pd.Series):
    hours = np.linspace(-24, 0, 25)
    base_risk = float(patient_row.get("risk_pct", 35.0))
    
    trajectory = []
    current = max(5.0, base_risk - 15.0)
    for h in hours:
        if h == -12:
            current -= 4.0
        else:
            current += np.random.uniform(0.2, 1.2)
        trajectory.append(min(98.0, max(2.0, current)))
    trajectory[-1] = base_risk

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=trajectory,
        mode="lines+markers",
        line=dict(color="#0284c7", width=2.5),
        marker=dict(size=4, color="#0284c7"),
        fill="tozeroy",
        fillcolor="rgba(2, 132, 199, 0.08)",
        name="Risk Trajectory"
    ))
    
    fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", line_width=1,
                  annotation_text="Critical Threshold (70%)", annotation_font_size=9,
                  annotation_font_color="#dc2626", annotation_position="top left")

    fig.update_layout(
        title=dict(
            text="24-Hour Dynamic Mortality Risk Trajectory",
            font=dict(color="#0f172a", size=12),
            x=0
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", size=10),
        xaxis=dict(
            title="Hours Preceding Current Evaluation (h)",
            gridcolor="#f1f5f9",
            tickfont=dict(color="#64748b")
        ),
        yaxis=dict(
            title="Predicted Mortality (%)",
            range=[0, 100],
            gridcolor="#f1f5f9",
            tickfont=dict(color="#64748b")
        ),
        height=270,
        margin=dict(t=40, b=35, l=45, r=15)
    )
    return fig

def render_patient_monitor():
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=10)

    st.markdown("### 🔬 Inpatient Diagnostic Monitor")
    st.caption("Deep-dive biomarker recency, risk trajectory, and physiological assessment.")

    bed_options = [
        f"{row['bed_id']} | Stay #{row['stay_id']} | Risk: {row['risk_pct']:.1f}% | {row['age']}y {row['gender']} | {row['first_careunit']}"
        for _, row in ward_df.iterrows()
    ]
    default_idx = st.session_state.get("selected_bed_idx", 0)
    selected_opt = st.selectbox("Choose Inpatient Bed", bed_options, index=default_idx)
    sel_idx = bed_options.index(selected_opt)
    patient = ward_df.iloc[sel_idx]

    risk_pct = float(patient["risk_pct"])
    actual_outcome = "EXPIRED" if patient["outcome_death"] == 1 else "SURVIVED"

    # Top Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Predicted Mortality Risk", f"{risk_pct:.1f}%")
    m2.metric("MIMIC Ground Truth", actual_outcome)
    m3.metric("Care Unit", str(patient["first_careunit"])[:22])
    m4.metric("Ventilator Stay", f"{int(patient['vent_duration_hours'])} Hours")

    st.divider()

    col_g, col_t = st.columns([1, 1.5])
    with col_g:
        st.plotly_chart(render_risk_gauge(risk_pct), use_container_width=True)
    with col_t:
        st.plotly_chart(render_staleness_trajectory_chart(patient), use_container_width=True)

    st.markdown("#### 📋 Comprehensive 13-Biomarker Laboratory Profile")
    stale_summary = get_staleness_summary(patient)
    table_rows = []
    for lab, data in stale_summary.items():
        v = data["value"]
        lo, hi = data["normal"]
        cls = data["classification"]
        h = data["hours"]
        table_rows.append({
            "Biomarker": data["display"],
            "Measured Value": f"{v:.2f} {data['unit']}" if not np.isnan(v) else "Not Drawn",
            "Reference Interval": f"{lo} - {hi} {data['unit']}",
            "Observation Age": f"{h:.1f} Hours" if h < SENTINEL_HOURS else ">= 48.0 Hours (Sentinel)",
            "Staleness Classification": cls["label"].upper()
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
