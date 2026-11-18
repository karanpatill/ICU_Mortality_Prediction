# patient_monitor.py - Individual Patient Bedside Deep-Dive
# AURA-ICU: Dynamic Clinical Decision Support System

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from components.utils import (
    load_model, load_schema, classify_risk, classify_staleness,
    get_staleness_summary, get_feature_importance, get_ward_patients,
    LAB_NAMES, LAB_DISPLAY, LAB_UNITS, LAB_NORMAL, SENTINEL_HOURS
)

def render_risk_gauge(risk_pct: float, patient_id: str = ""):
    """Render large Plotly risk gauge."""
    risk_cls = classify_risk(risk_pct)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_pct,
        number=dict(
            suffix="%",
            font=dict(color=risk_cls["color"], size=48, family="Segoe UI"),
            valueformat=".1f"
        ),
        delta=dict(reference=17.2, relative=False,
                   increasing=dict(color="#f85149"),
                   decreasing=dict(color="#3fb950"),
                   valueformat=".1f",
                   suffix="% vs avg"),
        title=dict(
            text=f"<b>MORTALITY RISK</b><br><span style='font-size:0.8em;color:#8b949e'>{risk_cls['label']}</span>",
            font=dict(color="#e6edf3", size=16)
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor="#30363d",
                tickfont=dict(color="#8b949e", size=10),
                tickvals=[0, 17, 25, 50, 70, 100],
                ticktext=["0%", "Avg", "25%", "50%", "70%", "100%"]
            ),
            bar=dict(color=risk_cls["color"], thickness=0.3),
            bgcolor="#161b22",
            borderwidth=0,
            steps=[
                dict(range=[0, 25], color="#0d2b12"),
                dict(range=[25, 50], color="#2b2200"),
                dict(range=[50, 70], color="#2b1600"),
                dict(range=[70, 100], color="#2b0a08"),
            ],
            threshold=dict(
                line=dict(color="#ffffff", width=2),
                thickness=0.9,
                value=17.2
            ),
        )
    ))
    fig.update_layout(
        paper_bgcolor="#1c2128",
        plot_bgcolor="#1c2128",
        font=dict(color="#e6edf3"),
        height=320,
        margin=dict(t=40, b=20, l=30, r=30),
    )
    return fig

def render_staleness_heatmap(staleness_data: dict):
    """Render staleness heatmap using Plotly."""
    labs = list(staleness_data.keys())
    display_names = [staleness_data[l]["display"] for l in labs]
    hours_vals = [min(staleness_data[l]["hours"], SENTINEL_HOURS) for l in labs]
    colors = [staleness_data[l]["classification"]["color"] for l in labs]
    labels_cls = [staleness_data[l]["classification"]["label"] for l in labs]
    values = [staleness_data[l]["value"] for l in labs]
    units = [staleness_data[l]["unit"] for l in labs]
    normals = [staleness_data[l]["normal"] for l in labs]

    # Custom hover text
    hover = []
    for i, lab in enumerate(labs):
        v = values[i]
        u = units[i]
        lo, hi = normals[i]
        h = hours_vals[i]
        status = ""
        if not np.isnan(v):
            if v < lo:
                status = " [LOW]"
            elif v > hi:
                status = " [HIGH]"
            else:
                status = " [NORMAL]"
        val_str = f"{v:.2f} {u}{status}" if not np.isnan(v) else "No data"
        hover.append(f"<b>{display_names[i]}</b><br>"
                     f"Value: {val_str}<br>"
                     f"Normal: {lo}-{hi} {u}<br>"
                     f"Last updated: {h:.1f}h ago<br>"
                     f"Status: <b>{labels_cls[i]}</b>")

    fig = go.Figure()

    # Horizontal bar chart showing staleness
    for i in range(len(labs)):
        h = hours_vals[i]
        pct = min(h / SENTINEL_HOURS * 100, 100)
        fig.add_trace(go.Bar(
            x=[h],
            y=[display_names[i]],
            orientation="h",
            marker=dict(color=colors[i], opacity=0.85),
            text=f"{h:.1f}h — {labels_cls[i]}",
            textposition="inside",
            insidetextfont=dict(color="#e6edf3", size=10),
            hovertext=hover[i],
            hoverinfo="text",
            showlegend=False,
        ))

    # Add threshold lines
    fig.add_vline(x=6, line_dash="dot", line_color="#3fb950", line_width=1,
                  annotation_text="Fresh→Moderate", annotation_position="top right",
                  annotation_font_size=9, annotation_font_color="#3fb950")
    fig.add_vline(x=20, line_dash="dot", line_color="#d29922", line_width=1,
                  annotation_text="Moderate→Stale", annotation_position="top right",
                  annotation_font_size=9, annotation_font_color="#d29922")
    fig.add_vline(x=48, line_dash="dot", line_color="#6e7681", line_width=1,
                  annotation_text="Sentinel", annotation_position="top right",
                  annotation_font_size=9, annotation_font_color="#6e7681")

    fig.update_layout(
        title=dict(text="LAB STALENESS HEATMAP", font=dict(color="#8b949e", size=12),
                   x=0, xanchor="left"),
        paper_bgcolor="#1c2128", plot_bgcolor="#1c2128",
        font=dict(color="#e6edf3", size=10),
        xaxis=dict(
            title="Hours Since Last Measurement",
            range=[0, 52],
            gridcolor="#21262d",
            tickfont=dict(color="#8b949e"),
            titlefont=dict(color="#8b949e", size=10),
        ),
        yaxis=dict(
            gridcolor="#21262d",
            tickfont=dict(color="#e6edf3", size=10),
        ),
        barmode="stack",
        height=380,
        margin=dict(t=40, b=50, l=90, r=20),
        bargap=0.25,
    )
    return fig

def render_feature_importance_chart(model, schema):
    """Render LightGBM feature importance (top 15, staleness highlighted)."""
    df_imp = get_feature_importance(model, schema, top_n=15)
    # Sort ascending for horizontal bar
    df_imp = df_imp.sort_values("importance", ascending=True)

    colors = ["#e3a008" if s else "#58a6ff" for s in df_imp["is_staleness"]]

    fig = go.Figure(go.Bar(
        x=df_imp["importance"],
        y=df_imp["display_name"],
        orientation="h",
        marker=dict(color=colors, opacity=0.9),
        hovertemplate="<b>%{y}</b><br>Split Importance: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="FEATURE IMPORTANCE (LightGBM Split Score)",
                   font=dict(color="#8b949e", size=12), x=0, xanchor="left"),
        paper_bgcolor="#1c2128", plot_bgcolor="#1c2128",
        font=dict(color="#e6edf3", size=10),
        xaxis=dict(title="Importance Score", gridcolor="#21262d",
                   tickfont=dict(color="#8b949e")),
        yaxis=dict(tickfont=dict(color="#e6edf3", size=10)),
        height=400,
        margin=dict(t=40, b=40, l=180, r=20),
        bargap=0.3,
        annotations=[
            dict(x=0.98, y=0.02, xref="paper", yref="paper",
                 text='<span style="color:#e3a008;">■</span> Staleness Feature &nbsp; '
                      '<span style="color:#58a6ff;">■</span> Value/Other Feature',
                 showarrow=False, font=dict(size=10, color="#8b949e"),
                 align="right")
        ]
    )
    return fig

def render_lab_values_table(staleness_data: dict):
    """Render lab values as styled table."""
    rows = []
    for lab, data in staleness_data.items():
        v = data["value"]
        lo, hi = data["normal"]
        cls = data["classification"]
        h = data["hours"]

        # Value status
        if np.isnan(v):
            val_str = "—"
            val_color = "#6e7681"
        elif v < lo:
            val_str = f"{v:.2f} {data['unit']} ↓"
            val_color = "#58a6ff"
        elif v > hi:
            val_str = f"{v:.2f} {data['unit']} ↑"
            val_color = "#f85149"
        else:
            val_str = f"{v:.2f} {data['unit']}"
            val_color = "#3fb950"

        hours_str = f"{h:.1f}h" if h < SENTINEL_HOURS else "≥48h"
        badge = f'<span style="background:{cls["color"]}22;color:{cls["color"]};padding:1px 6px;border-radius:3px;font-size:0.65rem;font-weight:700;">{cls["label"]}</span>'
        rows.append({
            "Lab": data["display"],
            "Value": f'<span style="color:{val_color};">{val_str}</span>',
            "Normal Range": f'{lo}–{hi} {data["unit"]}',
            "Last Measured": hours_str,
            "Staleness": badge,
        })

    df_table = pd.DataFrame(rows)
    table_html = df_table.to_html(escape=False, index=False,
                                  classes="lab-table",
                                  border=0)
    styled = f"""
    <style>
    .lab-table {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
    .lab-table th {{ 
        background:#21262d; color:#8b949e; font-weight:700; 
        letter-spacing:1px; text-transform:uppercase; font-size:0.65rem;
        padding:8px 12px; border-bottom:1px solid #30363d; text-align:left;
    }}
    .lab-table td {{ 
        padding:7px 12px; border-bottom:1px solid #21262d; color:#e6edf3; 
        vertical-align:middle;
    }}
    .lab-table tr:hover td {{ background:#21262d; }}
    </style>
    {table_html}
    """
    return styled

def render_patient_monitor():
    """Main patient monitor renderer."""
    model = load_model()
    schema = load_schema()
    ward_df = get_ward_patients(n_beds=12)

    # ── Patient selector ──────────────────────────────────────────────────────
    st.markdown('<p class="section-header">SELECT PATIENT</p>', unsafe_allow_html=True)

    bed_options = [f"{row['bed_id']} | {row['risk_pct']:.1f}% risk | Age {int(row['age'])} | {str(row['first_careunit'])[:25]}"
                   for _, row in ward_df.iterrows()]

    # Check if navigated from ward view
    default_idx = 0
    if st.session_state.get("selected_bed_idx") is not None:
        default_idx = int(st.session_state.selected_bed_idx)

    selected_opt = st.selectbox("Choose Patient Bed", bed_options, index=default_idx,
                                label_visibility="collapsed")
    sel_idx = int(selected_opt.split("|")[0].replace("BED-", "").strip()) - 1
    patient = ward_df.iloc[sel_idx]
    st.session_state.selected_bed_idx = sel_idx

    risk_pct = float(patient["risk_pct"])
    risk_cls = classify_risk(risk_pct)

    # ── Patient header ────────────────────────────────────────────────────────
    gender = "Male" if patient.get("gender") == "M" else "Female"
    age = int(patient.get("age", 0))
    unit = str(patient.get("first_careunit", "ICU"))
    vent_h = int(patient.get("vent_duration_hours", 0))
    actual = "EXPIRED" if int(patient.get("outcome_death", 0)) == 1 else "SURVIVED"
    actual_color = "#f85149" if actual == "EXPIRED" else "#3fb950"

    st.markdown(f"""
    <div style="background:#1c2128;border:1px solid #30363d;border-radius:10px;
                padding:16px 20px;margin-bottom:16px;
                border-left:4px solid {risk_cls['color']};">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:#e6edf3;">
                    {patient['bed_id']} &nbsp;
                    <span style="font-size:0.8rem;color:#8b949e;font-weight:400;">
                        {gender}, {age} years
                    </span>
                </div>
                <div style="font-size:0.8rem;color:#8b949e;margin-top:4px;">
                    {unit} &nbsp;|&nbsp; Vent Duration: {vent_h}h
                    &nbsp;|&nbsp; Admit: {str(patient.get('admission_type',''))[:20]}
                </div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:0.65rem;color:#8b949e;">MIMIC-IV Ground Truth:&nbsp;</span>
                <span style="font-size:0.75rem;font-weight:700;color:{actual_color};">{actual}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main layout: Gauge | Staleness heatmap ────────────────────────────────
    col_gauge, col_stale = st.columns([1, 2])

    with col_gauge:
        fig_gauge = render_risk_gauge(risk_pct)
        st.plotly_chart(fig_gauge, use_container_width=True, key="main_gauge")

        # Textual summary
        stale_data = get_staleness_summary(patient)
        n_stale = sum(1 for l in stale_data.values()
                      if l["classification"]["label"] in ("Stale", "Sentinel"))
        n_fresh = sum(1 for l in stale_data.values()
                      if l["classification"]["label"] == "Fresh")

        st.markdown(f"""
        <div class="info-box">
            <b>Key Drivers:</b><br>
            &bull; {n_stale}/13 labs have stale/sentinel readings<br>
            &bull; {n_fresh}/13 labs are freshly measured<br>
            &bull; Risk is <b>{risk_pct:.1f}%</b> vs ICU average 17.2%<br>
            &bull; Model: LightGBM (AUROC 0.8559)
        </div>
        """, unsafe_allow_html=True)

    with col_stale:
        fig_hm = render_staleness_heatmap(stale_data)
        st.plotly_chart(fig_hm, use_container_width=True, key="staleness_hm")

    # ── Lab values table ──────────────────────────────────────────────────────
    with st.expander("Detailed Lab Values & Staleness", expanded=True):
        table_html = render_lab_values_table(stale_data)
        st.markdown(table_html, unsafe_allow_html=True)

    # ── Feature importance ────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    fig_fi = render_feature_importance_chart(model, schema)
    st.plotly_chart(fig_fi, use_container_width=True, key="feat_imp")

    st.markdown("""
    <div class="info-box" style="margin-top:0;">
        <b>Note:</b> Feature importance shown is global (all 23,367 MIMIC-IV patients),
        not patient-specific. <span style="color:#e3a008;">Amber bars</span> = staleness features;
        <span style="color:#58a6ff;">Blue bars</span> = lab values / demographics.
        Staleness features contribute ~40% of total split importance, validating the
        Targeted Laboratory Staleness framework.
    </div>
    """, unsafe_allow_html=True)
