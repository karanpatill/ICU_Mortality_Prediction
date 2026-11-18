# ward_view.py - Central Nursing Station (12-bed ICU Ward Console)
# AURA-ICU: Clinical Decision Support System

import streamlit as st
import plotly.graph_objects as go
from components.utils import (
    get_ward_patients, classify_risk, LAB_NAMES, classify_staleness
)

def render_mini_staleness(patient_row):
    """Render a compact clinical staleness raster bar for bed card."""
    dots = ""
    for lab in LAB_NAMES:
        h = float(patient_row.get(f"{lab}_staleness", 48.0))
        cls = classify_staleness(h)
        dots += f'<span style="display:inline-block;width:7px;height:7px;border-radius:1px;background:{cls["color"]};margin:1px;" title="{lab}: {h:.1f}h"></span>'
    return dots

def render_ward_view():
    """Render the ICU Central Nursing Station grid with 12 bed monitors."""
    
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;border-bottom:1px solid #1c2738;padding-bottom:8px;">
        <div>
            <div style="font-family:var(--font-mono);font-size:0.68rem;color:#718096;letter-spacing:2px;text-transform:uppercase;">
                HOSPITAL INPATIENT SURVEILLANCE &bull; CENTRAL NURSING STATION (CNS)
            </div>
            <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:#edf2f7;letter-spacing:1px;">
                ACTIVE VENTILATED ICU BEDS (12-BED ADULT COHORT)
            </div>
        </div>
        <div style="font-family:var(--font-mono);font-size:0.72rem;color:#00e5ff;background:#090e15;padding:6px 12px;border:1px solid #1c2738;border-radius:4px;">
            REFRESH RATE: REAL-TIME &bull; DECAY MODEL: ON
        </div>
    </div>
    """, unsafe_allow_html=True)

    ward_df = get_ward_patients(n_beds=12)

    # ── Top metrics bar ───────────────────────────────────────────────────────
    total = len(ward_df)
    n_critical = (ward_df["risk_pct"] >= 70).sum()
    n_elevated = ((ward_df["risk_pct"] >= 50) & (ward_df["risk_pct"] < 70)).sum()
    n_watch    = ((ward_df["risk_pct"] >= 25) & (ward_df["risk_pct"] < 50)).sum()
    n_stable   = (ward_df["risk_pct"] < 25).sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div style="background:#080d14;border:1px solid #1c2738;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#718096;text-transform:uppercase;">CENSUS OCCUPANCY</div>
            <div style="font-family:var(--font-display);font-size:1.6rem;color:#00e5ff;font-weight:700;">{total} / 12</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div style="background:#080d14;border:1px solid #1c2738;border-top:3px solid #ff1744;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#ff8097;text-transform:uppercase;">CRITICAL (&gt;70%)</div>
            <div style="font-family:var(--font-display);font-size:1.6rem;color:#ff1744;font-weight:700;">{n_critical}</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div style="background:#080d14;border:1px solid #1c2738;border-top:3px solid #ff9100;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#ffb74d;text-transform:uppercase;">ELEVATED (50-70%)</div>
            <div style="font-family:var(--font-display);font-size:1.6rem;color:#ff9100;font-weight:700;">{n_elevated}</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div style="background:#080d14;border:1px solid #1c2738;border-top:3px solid #ffd600;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#ffe082;text-transform:uppercase;">WATCH (25-50%)</div>
            <div style="font-family:var(--font-display);font-size:1.6rem;color:#ffd600;font-weight:700;">{n_watch}</div>
        </div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div style="background:#080d14;border:1px solid #1c2738;border-top:3px solid #00e676;border-radius:4px;padding:8px 12px;text-align:center;">
            <div style="font-family:var(--font-mono);font-size:0.62rem;color:#69f0ae;text-transform:uppercase;">STABLE (&lt;25%)</div>
            <div style="font-family:var(--font-display);font-size:1.6rem;color:#00e676;font-weight:700;">{n_stable}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── 12-Bed Telemetry Grid ─────────────────────────────────────────────────
    for row_idx in range(4):
        cols = st.columns(3)
        for col_idx in range(3):
            bed_num = row_idx * 3 + col_idx
            if bed_num >= len(ward_df):
                break
            patient = ward_df.iloc[bed_num]
            risk_pct = float(patient["risk_pct"])
            risk_cls = classify_risk(risk_pct)

            gender_sym = "M" if patient.get("gender") == "M" else "F"
            age = int(patient.get("age", 0))
            unit = str(patient.get("first_careunit", "ICU"))
            vent_h = int(patient.get("vent_duration_hours", 0))
            dots = render_mini_staleness(patient)
            
            # Clinical Alarm Style
            alarm_class = "alarm-critical" if risk_pct >= 70 else ("alarm-elevated" if risk_pct >= 50 else ("alarm-watch" if risk_pct >= 25 else "alarm-stable"))

            with cols[col_idx]:
                st.markdown(f"""
                <div class="cns-bed-card {alarm_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-family:var(--font-mono);font-size:0.75rem;font-weight:700;color:#edf2f7;letter-spacing:1px;">
                            {patient['bed_id']}
                        </span>
                        <span style="font-family:var(--font-mono);font-size:0.62rem;font-weight:700;color:{risk_cls['color']};background:rgba(255,255,255,0.04);padding:2px 6px;border-radius:3px;">
                            {risk_cls['label']}
                        </span>
                    </div>
                    <div style="display:flex;align-items:baseline;justify-content:space-between;margin:8px 0 4px 0;">
                        <span style="font-family:var(--font-display);font-size:2.2rem;font-weight:700;color:{risk_cls['color']};line-height:1;">
                            {risk_pct:.1f}<span style="font-size:1.1rem;">%</span>
                        </span>
                        <span style="font-family:var(--font-mono);font-size:0.65rem;color:#718096;">
                            IMV: {vent_h}h &bull; {gender_sym}/{age}y
                        </span>
                    </div>
                    <div style="font-family:var(--font-mono);font-size:0.65rem;color:#718096;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:6px;">
                        {unit[:22]}
                    </div>
                    <div style="padding-top:4px;border-top:1px solid #142030;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-family:var(--font-mono);font-size:0.58rem;color:#718096;">LAB MATRIX:</span>
                        <div>{dots}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"SELECT BED {bed_num+1:02d}", key=f"cns_btn_{bed_num}", use_container_width=True):
                    st.session_state.selected_bed_idx = bed_num
                    st.session_state.go_to_monitor = True
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
