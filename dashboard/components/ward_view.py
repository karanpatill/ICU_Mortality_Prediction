# ward_view.py - Virtual ICU Ward (12-bed grid view)
# AURA-ICU: Dynamic Clinical Decision Support System

import streamlit as st
import plotly.graph_objects as go
from components.utils import (
    get_ward_patients, classify_risk, LAB_NAMES, classify_staleness
)

def render_mini_staleness(patient_row):
    """Render a compact staleness bar for the bed card."""
    colors = []
    for lab in LAB_NAMES:
        h = float(patient_row.get(f"{lab}_staleness", 48.0))
        cls = classify_staleness(h)
        colors.append(cls["color"])
    # Create a 13-cell mini heatmap as colored dots
    dots = ""
    for c in colors:
        dots += f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin:1px;"></span>'
    return dots

def render_ward_view():
    """Render the full ICU ward grid with 12 patient bed cards."""
    
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <span class="section-header">VIRTUAL ICU WARD — REAL-TIME MORTALITY RISK OVERVIEW</span>
    </div>
    """, unsafe_allow_html=True)

    # Load ward patients
    with st.spinner("Loading patient data from MIMIC-IV..."):
        ward_df = get_ward_patients(n_beds=12)

    # ── Top metrics bar ───────────────────────────────────────────────────────
    total = len(ward_df)
    n_critical = (ward_df["risk_pct"] >= 70).sum()
    n_elevated = ((ward_df["risk_pct"] >= 50) & (ward_df["risk_pct"] < 70)).sum()
    n_watch    = ((ward_df["risk_pct"] >= 25) & (ward_df["risk_pct"] < 50)).sum()
    n_stable   = (ward_df["risk_pct"] < 25).sum()
    avg_risk   = ward_df["risk_pct"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value" style="color:#58a6ff">{total}</span>
            <div class="metric-label">Total Patients</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value" style="color:#f85149">{n_critical}</span>
            <div class="metric-label">Critical</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value" style="color:#fd8c73">{n_elevated}</span>
            <div class="metric-label">Elevated</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value" style="color:#e3b341">{n_watch}</span>
            <div class="metric-label">Watch</div>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value" style="color:#3fb950">{n_stable}</span>
            <div class="metric-label">Stable</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Risk distribution donut ───────────────────────────────────────────────
    with st.expander("Ward Risk Distribution", expanded=False):
        fig_donut = go.Figure(go.Pie(
            labels=["Critical (>70%)", "Elevated (50-70%)", "Watch (25-50%)", "Stable (<25%)"],
            values=[n_critical, n_elevated, n_watch, n_stable],
            hole=0.6,
            marker=dict(colors=["#f85149", "#fd8c73", "#e3b341", "#3fb950"]),
            textinfo="label+percent",
            textfont=dict(color="#e6edf3", size=11),
        ))
        fig_donut.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            showlegend=False, height=280, margin=dict(t=10, b=10, l=10, r=10),
            annotations=[dict(text=f"<b>{avg_risk:.1f}%</b><br>Avg Risk",
                              x=0.5, y=0.5, font_size=14, showarrow=False,
                              font=dict(color="#e6edf3"))]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── 12-bed grid ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">PATIENT BED GRID — Click a bed to view full patient monitor</p>',
                unsafe_allow_html=True)

    # Store selected patient in session state
    if "selected_bed_idx" not in st.session_state:
        st.session_state.selected_bed_idx = None
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = 0

    # Render 4 rows × 3 cols
    for row_idx in range(4):
        cols = st.columns(3)
        for col_idx in range(3):
            bed_num = row_idx * 3 + col_idx
            if bed_num >= len(ward_df):
                break
            patient = ward_df.iloc[bed_num]
            risk_pct = float(patient["risk_pct"])
            risk_cls = classify_risk(risk_pct)
            level = risk_cls["label"].lower()

            gender_sym = "M" if patient.get("gender") == "M" else "F"
            age = int(patient.get("age", 0))
            unit = str(patient.get("first_careunit", "ICU"))
            # Abbreviate unit name
            unit_abbr = unit.replace("Intensive Care Unit", "ICU")\
                             .replace("Medical ", "M-")\
                             .replace("Surgical ", "S-")\
                             .replace("Trauma ", "T-")\
                             .replace("Neuro ", "N-")\
                             .replace("(", "").replace(")", "")
            if len(unit_abbr) > 18:
                unit_abbr = unit_abbr[:18] + "..."
            vent_h = int(patient.get("vent_duration_hours", 0))
            dots = render_mini_staleness(patient)

            with cols[col_idx]:
                # Plotly risk gauge (mini)
                fig_mini = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=risk_pct,
                    number=dict(suffix="%", font=dict(color=risk_cls["color"], size=22)),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickfont=dict(color="#8b949e", size=8),
                                  tickvals=[0, 25, 50, 70, 100]),
                        bar=dict(color=risk_cls["color"], thickness=0.4),
                        bgcolor="#21262d",
                        steps=[
                            dict(range=[0, 25], color="#0a2d0f"),
                            dict(range=[25, 50], color="#2d2200"),
                            dict(range=[50, 70], color="#2d1a00"),
                            dict(range=[70, 100], color="#2d0a0d"),
                        ],
                        threshold=dict(
                            line=dict(color=risk_cls["color"], width=2),
                            thickness=0.8,
                            value=risk_pct
                        ),
                        borderwidth=0,
                    )
                ))
                fig_mini.update_layout(
                    paper_bgcolor="#1c2128", plot_bgcolor="#1c2128",
                    height=130, margin=dict(t=10, b=0, l=10, r=10),
                    font=dict(color="#e6edf3")
                )
                st.plotly_chart(fig_mini, use_container_width=True, key=f"gauge_{bed_num}")

                # Bed info
                st.markdown(f"""
                <div style="text-align:center; margin-top:-10px; padding:0 4px;">
                    <div style="font-size:0.65rem;color:#8b949e;letter-spacing:1px;">{patient['bed_id']}</div>
                    <div style="font-size:0.68rem;font-weight:600;color:{risk_cls['color']};
                                background:rgba(0,0,0,0.3);border-radius:4px;padding:1px 6px;
                                display:inline-block;letter-spacing:1px;">{risk_cls['label']}</div>
                    <div style="font-size:0.68rem;color:#8b949e;margin-top:3px;">
                        {gender_sym}, {age}y | Vent: {vent_h}h
                    </div>
                    <div style="font-size:0.65rem;color:#6e7681;margin:2px 0;">{unit_abbr}</div>
                    <div style="margin-top:4px;">{dots}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"View Patient", key=f"btn_{bed_num}",
                             use_container_width=True):
                    st.session_state.selected_bed_idx = bed_num
                    st.session_state.selected_patient = patient.to_dict()
                    st.session_state.go_to_monitor = True
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;gap:16px;align-items:center;margin-top:12px;
                padding:10px 16px;background:#161b22;border-radius:8px;
                border:1px solid #30363d;flex-wrap:wrap;">
        <span style="font-size:0.7rem;color:#8b949e;font-weight:700;letter-spacing:1px;">RISK LEGEND:</span>
        <span style="font-size:0.72rem;color:#f85149;">&#9632; CRITICAL (&gt;70%)</span>
        <span style="font-size:0.72rem;color:#fd8c73;">&#9632; ELEVATED (50-70%)</span>
        <span style="font-size:0.72rem;color:#e3b341;">&#9632; WATCH (25-50%)</span>
        <span style="font-size:0.72rem;color:#3fb950;">&#9632; STABLE (&lt;25%)</span>
        <span style="margin-left:auto;font-size:0.7rem;color:#8b949e;">
            Lab Dots: 
            <span style="color:#3fb950;">&#9679;</span> Fresh (&lt;6h)&nbsp;
            <span style="color:#d29922;">&#9679;</span> Moderate (6-20h)&nbsp;
            <span style="color:#f85149;">&#9679;</span> Stale (20-48h)&nbsp;
            <span style="color:#6e7681;">&#9679;</span> Sentinel (&ge;48h)
        </span>
    </div>
    """, unsafe_allow_html=True)
