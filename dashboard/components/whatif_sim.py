# whatif_sim.py - What-If Clinician Simulator
# AURA-ICU: Dynamic Clinical Decision Support System

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from components.utils import (
    load_model, load_schema, classify_risk, whatif_predict,
    get_ward_patients, SENTINEL_HOURS
)

def render_risk_comparison(before_pct: float, after_pct: float):
    """Render before/after risk comparison as side-by-side gauges."""
    before_cls = classify_risk(before_pct)
    after_cls = classify_risk(after_pct)
    delta = after_pct - before_pct
    delta_color = "#f85149" if delta > 0 else "#3fb950"
    delta_arrow = "▲" if delta > 0 else "▼"
    delta_str = f"{delta_arrow} {abs(delta):.1f}%"

    fig = go.Figure()
    # Before gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=before_pct,
        number=dict(suffix="%", font=dict(color=before_cls["color"], size=28),
                    valueformat=".1f"),
        title=dict(text="<b>BEFORE</b><br><span style='font-size:0.8em;color:#8b949e'>Baseline Risk</span>",
                   font=dict(color="#8b949e", size=12)),
        domain=dict(x=[0, 0.45], y=[0, 1]),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color="#6e7681", size=8)),
            bar=dict(color=before_cls["color"], thickness=0.3),
            bgcolor="#161b22", borderwidth=0,
            steps=[dict(range=[0, 100], color="#21262d")],
        )
    ))
    # After gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=after_pct,
        number=dict(suffix="%", font=dict(color=after_cls["color"], size=28),
                    valueformat=".1f"),
        title=dict(text="<b>AFTER</b><br><span style='font-size:0.8em;color:#8b949e'>Modified Risk</span>",
                   font=dict(color="#8b949e", size=12)),
        domain=dict(x=[0.55, 1.0], y=[0, 1]),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color="#6e7681", size=8)),
            bar=dict(color=after_cls["color"], thickness=0.3),
            bgcolor="#161b22", borderwidth=0,
            steps=[dict(range=[0, 100], color="#21262d")],
        )
    ))

    fig.update_layout(
        paper_bgcolor="#1c2128", plot_bgcolor="#1c2128",
        font=dict(color="#e6edf3"),
        height=250, margin=dict(t=60, b=20, l=20, r=20),
        annotations=[
            dict(x=0.5, y=0.5, xref="paper", yref="paper",
                 text=f"<b style='font-size:20px;color:{delta_color};'>{delta_str}</b>",
                 showarrow=False, font=dict(size=20, color=delta_color))
        ]
    )
    return fig

def render_whatif_sim():
    """Main What-If Simulator renderer."""
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=12)

    st.markdown("""
    <div style="margin-bottom:12px;">
        <span class="section-header">WHAT-IF CLINICIAN SIMULATOR</span>
        <p style="color:#8b949e;font-size:0.82rem;margin-top:6px;">
            Adjust clinical parameters using sliders below to see how changes would affect
            predicted mortality risk. This simulates clinical interventions (e.g., refreshing
            a stale lab test, improving a lab value) in real-time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Patient selector ──────────────────────────────────────────────────────
    bed_options = [
        f"{row['bed_id']} | {row['risk_pct']:.1f}% | {str(row['first_careunit'])[:20]}"
        for _, row in ward_df.iterrows()
    ]
    default_idx = st.session_state.get("selected_bed_idx", 0)
    selected = st.selectbox("Select Patient for Simulation", bed_options,
                            index=default_idx, key="whatif_selector")
    sel_idx = int(selected.split("|")[0].replace("BED-", "").strip()) - 1
    patient = ward_df.iloc[sel_idx]
    baseline_risk = float(patient["risk_pct"]) / 100.0

    st.markdown(f"""
    <div style="background:#1c2128;border:1px solid #30363d;border-radius:8px;
                padding:12px 16px;margin-bottom:16px;">
        <b style="color:#e6edf3;">{patient['bed_id']}</b>
        <span style="color:#8b949e;"> | Age {int(patient['age'])} | 
        {str(patient.get('first_careunit',''))[:30]} | 
        Baseline Risk: </span>
        <b style="color:{classify_risk(float(patient['risk_pct']))['color']};">
            {patient['risk_pct']:.1f}%
        </b>
    </div>
    """, unsafe_allow_html=True)

    # ── Sliders ───────────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">ADJUST CLINICAL PARAMETERS</p>',
                unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    overrides = {}

    with col_left:
        st.markdown("**Lab Values**")

        # Lactate
        cur_lac = float(patient.get("lactate_val", 2.0))
        new_lac = st.slider(
            "Lactate (mmol/L) — Normal: 0.5-2.0",
            min_value=0.5, max_value=15.0,
            value=round(cur_lac, 1), step=0.1,
            key="wi_lactate_val",
            help="High lactate indicates tissue hypoxia — key mortality predictor"
        )
        if abs(new_lac - cur_lac) > 0.05:
            overrides["lactate_val"] = new_lac

        # PaO2
        cur_pao2 = float(patient.get("pao2_val", 85.0))
        new_pao2 = st.slider(
            "PaO2 (mmHg) — Normal: 75-100",
            min_value=30.0, max_value=200.0,
            value=round(cur_pao2, 0), step=1.0,
            key="wi_pao2_val",
            help="Arterial oxygen partial pressure — indicates respiratory status"
        )
        if abs(new_pao2 - cur_pao2) > 0.5:
            overrides["pao2_val"] = new_pao2

        # Creatinine
        cur_cr = float(patient.get("creatinine_val", 1.0))
        new_cr = st.slider(
            "Creatinine (mg/dL) — Normal: 0.6-1.2",
            min_value=0.3, max_value=15.0,
            value=round(cur_cr, 1), step=0.1,
            key="wi_creatinine_val",
            help="Kidney function marker"
        )
        if abs(new_cr - cur_cr) > 0.05:
            overrides["creatinine_val"] = new_cr

        # Age
        cur_age = int(patient.get("age", 65))
        new_age = st.slider(
            "Patient Age (years)",
            min_value=18, max_value=100,
            value=cur_age, step=1,
            key="wi_age",
            help="Age is a significant risk factor"
        )
        if new_age != cur_age:
            overrides["age"] = new_age

    with col_right:
        st.markdown("**Lab Staleness (hours since last measurement)**")

        # Lactate staleness
        cur_ls = float(patient.get("lactate_staleness", 24.0))
        new_ls = st.slider(
            "Lactate Staleness (hours)",
            min_value=0.0, max_value=48.0,
            value=round(min(cur_ls, 48.0), 1), step=0.5,
            key="wi_lactate_staleness",
            help="Slide to 0 to simulate a fresh lactate measurement"
        )
        if abs(new_ls - cur_ls) > 0.1:
            overrides["lactate_staleness"] = new_ls

        # PaO2 staleness
        cur_ps = float(patient.get("pao2_staleness", 12.0))
        new_ps = st.slider(
            "PaO2 Staleness (hours)",
            min_value=0.0, max_value=48.0,
            value=round(min(cur_ps, 48.0), 1), step=0.5,
            key="wi_pao2_staleness",
            help="Slide to 0 to simulate a fresh blood gas"
        )
        if abs(new_ps - cur_ps) > 0.1:
            overrides["pao2_staleness"] = new_ps

        # Bilirubin staleness
        cur_bs = float(patient.get("bilirubin_staleness", 24.0))
        new_bs = st.slider(
            "Bilirubin Staleness (hours)",
            min_value=0.0, max_value=48.0,
            value=round(min(cur_bs, 48.0), 1), step=0.5,
            key="wi_bilirubin_staleness",
            help="Liver function marker staleness"
        )
        if abs(new_bs - cur_bs) > 0.1:
            overrides["bilirubin_staleness"] = new_bs

        # Creatinine staleness
        cur_cs = float(patient.get("creatinine_staleness", 12.0))
        new_cs = st.slider(
            "Creatinine Staleness (hours)",
            min_value=0.0, max_value=48.0,
            value=round(min(cur_cs, 48.0), 1), step=0.5,
            key="wi_creatinine_staleness",
            help="Kidney function marker staleness"
        )
        if abs(new_cs - cur_cs) > 0.1:
            overrides["creatinine_staleness"] = new_cs

    # ── Compute new risk ──────────────────────────────────────────────────────
    before_pct = float(patient["risk_pct"])

    if overrides:
        new_risk_raw = whatif_predict(patient, overrides, model, schema)
        after_pct = new_risk_raw * 100
    else:
        after_pct = before_pct

    # ── Show comparison ───────────────────────────────────────────────────────
    st.markdown('<p class="section-header">RISK COMPARISON</p>',
                unsafe_allow_html=True)

    fig_cmp = render_risk_comparison(before_pct, after_pct)
    st.plotly_chart(fig_cmp, use_container_width=True, key="whatif_comparison")

    # ── Delta analysis ────────────────────────────────────────────────────────
    delta = after_pct - before_pct
    before_label = classify_risk(before_pct)["label"]
    after_label = classify_risk(after_pct)["label"]
    before_color = classify_risk(before_pct)["color"]
    after_color = classify_risk(after_pct)["color"]

    if not overrides:
        box_style = "info-box"
        summary = "No parameters changed. Adjust sliders above to simulate clinical interventions."
    elif delta < -5:
        box_style = "info-box"
        summary = (f"Intervention IMPROVES predicted outcome. Risk decreased by "
                   f"<b>{abs(delta):.1f}%</b>. "
                   f"Status: <span style='color:{before_color};'>{before_label}</span> "
                   f"&rarr; <span style='color:{after_color};'>{after_label}</span>. "
                   f"Consider ordering fresh lab tests to reduce staleness uncertainty.")
    elif delta > 5:
        box_style = "warning-box"
        summary = (f"Simulated change WORSENS predicted outcome. Risk increased by "
                   f"<b>{abs(delta):.1f}%</b>. "
                   f"Status: <span style='color:{before_color};'>{before_label}</span> "
                   f"&rarr; <span style='color:{after_color};'>{after_label}</span>. "
                   f"Clinician attention required.")
    else:
        box_style = "info-box"
        summary = (f"Minimal change in predicted risk ({delta:+.1f}%). "
                   f"Current intervention has limited effect on model prediction.")

    st.markdown(f'<div class="{box_style}">{summary}</div>', unsafe_allow_html=True)

    # ── Applied overrides summary ─────────────────────────────────────────────
    if overrides:
        st.markdown('<p class="section-header" style="margin-top:16px;">APPLIED CHANGES</p>',
                    unsafe_allow_html=True)
        for col, val in overrides.items():
            orig = float(patient.get(col, 0))
            arrow = "↑" if val > orig else "↓"
            unit_map = {
                "lactate_val": "mmol/L", "pao2_val": "mmHg", "creatinine_val": "mg/dL",
                "age": "yrs", "lactate_staleness": "h", "pao2_staleness": "h",
                "bilirubin_staleness": "h", "creatinine_staleness": "h"
            }
            u = unit_map.get(col, "")
            col_display = col.replace("_val", "").replace("_staleness", " staleness").replace("_", " ").title()
            st.markdown(
                f"- **{col_display}**: {orig:.1f} → {val:.1f} {u} {arrow}"
            )

    # ── Clinical insight ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="info-box" style="margin-top:16px;">
        <b>How This Works:</b> The model (LightGBM, AUROC 0.8559) uses both lab <i>values</i>
        and lab <i>staleness</i> as features. When a lab result is stale (measured long ago),
        the model is less certain about the patient's current state — increasing predicted risk.
        Ordering a fresh measurement reduces staleness to ~0h, often meaningfully lowering
        the predicted mortality probability.
    </div>
    """, unsafe_allow_html=True)

    # ── Reset button ──────────────────────────────────────────────────────────
    if st.button("Reset All Sliders to Baseline", key="wi_reset"):
        # Clear What-If session state keys
        for key in list(st.session_state.keys()):
            if key.startswith("wi_"):
                del st.session_state[key]
        st.rerun()
