"""
generate_methodology_diagram.py
Generates a publication-quality vector diagram illustrating the Targeted Laboratory Staleness
framework and prospective landmark evaluation pipeline.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

def create_methodology_diagram():
    # Set figure dimensions (wide publication format: ~11.5 x 4.8 inches)
    fig, ax = plt.subplots(figsize=(12.0, 4.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis('off')
    
    # Typography styling
    font_main = {'fontsize': 9, 'color': '#0f172a', 'family': 'sans-serif'}
    font_bold = {'fontsize': 9.5, 'color': '#0f172a', 'weight': 'bold', 'family': 'sans-serif'}
    font_title = {'fontsize': 10.5, 'color': '#0f172a', 'weight': 'bold', 'family': 'sans-serif'}
    font_small = {'fontsize': 8, 'color': '#475569', 'family': 'sans-serif'}
    font_code = {'fontsize': 8, 'color': '#1e293b', 'family': 'monospace', 'weight': 'bold'}

    # -------------------------------------------------------------------------
    # STAGE 1: RAW ICU STREAM & CLINICAL DATA INGESTION
    # -------------------------------------------------------------------------
    # Bounding Box 1
    p1 = FancyBboxPatch((2, 3), 20, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                         facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.2)
    ax.add_patch(p1)
    
    # Header 1
    ax.text(12, 34.5, "1. ICU Longitudinal Stream", ha='center', va='center', **font_title)
    ax.text(12, 32.5, "Landmark Window [t_in, t_landmark]", ha='center', va='center', **font_small)
    
    # Sub-card: Continuous Vitals
    cv = FancyBboxPatch((3.5, 20), 17, 10.5, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#ffffff', edgecolor='#94a3b8', linewidth=0.8)
    ax.add_patch(cv)
    ax.text(12, 28.5, "Continuous Vitals (V_cont)", ha='center', va='center', **font_bold)
    ax.text(12, 26.2, "HR, MAP, SpO2, RespRate", ha='center', va='center', **font_code)
    ax.text(12, 24.0, "• High-frequency monitors", ha='center', va='center', **font_small)
    ax.text(12, 22.0, "• Latest value preserved", ha='center', va='center', **font_small)
    ax.text(12, 20.6, "• Zero artificial time-decay", ha='center', va='center', **font_small)

    # Sub-card: Intermittent Labs
    il = FancyBboxPatch((3.5, 5), 17, 13, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#eff6ff', edgecolor='#93c5fd', linewidth=0.8)
    ax.add_patch(il)
    ax.text(12, 16.2, "Intermittent Labs (L_intermit)", ha='center', va='center', **font_bold)
    ax.text(12, 14.2, "Lactate, PaO2, Bilirubin, pH...", ha='center', va='center', **font_code)
    ax.text(12, 12.0, "• Ordered discretely by MDs", ha='center', va='center', **font_small)
    ax.text(12, 10.0, "• Missing Not At Random", ha='center', va='center', **font_small)
    ax.text(12, 8.0, "• Highly sparse time-series", ha='center', va='center', **font_small)
    ax.text(12, 6.2, "• No naive forward-filling", ha='center', va='center', **font_small)

    # -------------------------------------------------------------------------
    # ARROW 1 -> 2
    # -------------------------------------------------------------------------
    ax.annotate('', xy=(24.5, 20), xytext=(22.5, 20),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))

    # -------------------------------------------------------------------------
    # STAGE 2: TARGETED STALENESS & SENTINEL ENCODING
    # -------------------------------------------------------------------------
    p2 = FancyBboxPatch((25, 3), 25, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                         facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.2)
    ax.add_patch(p2)
    
    ax.text(37.5, 34.5, "2. Targeted Staleness Engine", ha='center', va='center', **font_title)
    ax.text(37.5, 32.5, "Transforming Sparsity into Clinical Signals", ha='center', va='center', **font_small)

    # Sub-card: Elapsed Time Formulation
    et = FancyBboxPatch((26.5, 19.5), 22, 11, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#ffffff', edgecolor='#64748b', linewidth=0.8)
    ax.add_patch(et)
    ax.text(37.5, 28.5, "Measured Test Formulation", ha='center', va='center', **font_bold)
    ax.text(37.5, 26.0, r"$\Delta t_{i,j} = t_{\mathrm{landmark}} - \max(\mathcal{T}_{i,j})$", 
            ha='center', va='center', fontsize=9.5, color='#0f172a')
    ax.text(37.5, 23.5, r"Short $\Delta t$ ($\leq 2\mathrm{h}$): Active Bedside Crisis", ha='center', va='center', fontsize=7.5, color='#b91c1c', weight='bold')
    ax.text(37.5, 21.0, r"Long $\Delta t$ ($\geq 20\mathrm{h}$): Clinician-Observed Stability", ha='center', va='center', fontsize=7.5, color='#047857', weight='bold')

    # Sub-card: Sentinel Encoding
    se = FancyBboxPatch((26.5, 5), 22, 12.5, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#fefce8', edgecolor='#fde047', linewidth=0.8)
    ax.add_patch(se)
    ax.text(37.5, 15.5, "Sentinel Encoding (Unmeasured)", ha='center', va='center', **font_bold)
    ax.text(37.5, 13.0, r"$\Delta t_{i,j} = 2 \times T = 48.0\ \mathrm{hours}$", 
            ha='center', va='center', fontsize=9.5, color='#854d0e')
    ax.text(37.5, 10.5, "• Prevents NaN runtime exceptions", ha='center', va='center', **font_small)
    ax.text(37.5, 8.5, "• Isolates patients with zero pathology", ha='center', va='center', **font_small)
    ax.text(37.5, 6.5, "• Tree-Split Isolation Property", ha='center', va='center', fontsize=8, color='#b45309', weight='bold')

    # -------------------------------------------------------------------------
    # ARROW 2 -> 3
    # -------------------------------------------------------------------------
    ax.annotate('', xy=(52.5, 20), xytext=(50.5, 20),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))

    # -------------------------------------------------------------------------
    # STAGE 3: GBDT TREE-SPLIT LEARNING & FEATURE ENSEMBLE
    # -------------------------------------------------------------------------
    p3 = FancyBboxPatch((53, 3), 22, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                         facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.2)
    ax.add_patch(p3)

    ax.text(64, 34.5, "3. Gradient Boosted Trees", ha='center', va='center', **font_title)
    ax.text(64, 32.5, "LightGBM / XGBoost Ensembles", ha='center', va='center', **font_small)

    # Sub-card: Feature Space Concatenation
    fs = FancyBboxPatch((54.5, 21), 19, 9.5, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#ffffff', edgecolor='#64748b', linewidth=0.8)
    ax.add_patch(fs)
    ax.text(64, 28.5, "Concatenated Feature Vector", ha='center', va='center', **font_bold)
    ax.text(64, 26.2, r"$\mathbf{x} = [X_{\mathrm{vitals}}, X_{\mathrm{labs}}, \mathbf{\Delta t}, X_{\mathrm{vent}}]$", ha='center', va='center', fontsize=8.5, color='#0f172a')
    ax.text(64, 24.0, "• 13 Targeted Staleness features", ha='center', va='center', **font_small)
    ax.text(64, 22.0, "• Mechanical ventilator mechanics", ha='center', va='center', **font_small)

    # Sub-card: Tree Split Mechanism
    ts = FancyBboxPatch((54.5, 5), 19, 14, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#f0fdf4', edgecolor='#86efac', linewidth=0.8)
    ax.add_patch(ts)
    ax.text(64, 17.2, "Optimal Tree Partitioning", ha='center', va='center', **font_bold)
    ax.text(64, 15.0, r"Threshold Splits on $\Delta t$:", ha='center', va='center', fontsize=8, color='#166534', weight='bold')
    ax.text(64, 13.0, r"$\tau < 6\mathrm{h} \rightarrow$ Active serial deterioration", ha='center', va='center', fontsize=7.5, color='#15803d')
    ax.text(64, 11.0, r"$\tau \in [12, 24\mathrm{h}] \rightarrow$ Stable recovery", ha='center', va='center', fontsize=7.5, color='#15803d')
    ax.text(64, 9.0, r"$\tau = 48\mathrm{h} \rightarrow$ Sentinel extreme branch", ha='center', va='center', fontsize=7.5, color='#15803d')
    ax.text(64, 6.5, "< 5ms CPU Latency (No GPU)", ha='center', va='center', fontsize=8, color='#047857', weight='bold')

    # -------------------------------------------------------------------------
    # ARROW 3 -> 4
    # -------------------------------------------------------------------------
    ax.annotate('', xy=(77.5, 20), xytext=(75.5, 20),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=1.5))

    # -------------------------------------------------------------------------
    # STAGE 4: CLINICAL BEDSIDE OUTPUT & EXPLAINABILITY
    # -------------------------------------------------------------------------
    p4 = FancyBboxPatch((78, 3), 20, 34, boxstyle="round,pad=0.8,rounding_size=1.5",
                         facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.2)
    ax.add_patch(p4)

    ax.text(88, 34.5, "4. Bedside Risk Intelligence", ha='center', va='center', **font_title)
    ax.text(88, 32.5, "Actionable Real-Time Guidance", ha='center', va='center', **font_small)

    # Sub-card: Calibrated Risk Score
    rs = FancyBboxPatch((79.5, 21), 17, 9.5, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#ffffff', edgecolor='#e2e8f0', linewidth=0.8)
    ax.add_patch(rs)
    ax.text(88, 28.5, "Calibrated Probability", ha='center', va='center', **font_bold)
    ax.text(88, 26.0, r"$P(\mathrm{Mortality} \mid \mathbf{x}, \mathbf{\Delta t})$", ha='center', va='center', fontsize=9.5, color='#0f172a')
    ax.text(88, 23.5, "AUROC: 0.8559 (+0.319%)", ha='center', va='center', fontsize=8, color='#1e40af', weight='bold')
    ax.text(88, 22.0, "AUPRC: 0.5854 (+0.415%)", ha='center', va='center', fontsize=8, color='#1e40af', weight='bold')

    # Sub-card: SHAP Bedside Explanations
    sh = FancyBboxPatch((79.5, 5), 17, 14, boxstyle="round,pad=0.5,rounding_size=1.0",
                         facecolor='#faf5ff', edgecolor='#d8b4fe', linewidth=0.8)
    ax.add_patch(sh)
    ax.text(88, 17.2, "SHAP Local Attribution", ha='center', va='center', **font_bold)
    ax.text(88, 14.8, '"Elevated Risk (64%):', ha='center', va='center', fontsize=8, color='#6b21a8', style='italic')
    ax.text(88, 12.8, '• Rising Lactate (3.4 mmol/L)', ha='center', va='center', fontsize=7.5, color='#581c87')
    ax.text(88, 10.8, '• PaO2 Staleness (Δt = 1.1h)', ha='center', va='center', fontsize=7.5, color='#581c87', weight='bold')
    ax.text(88, 8.8, '• Driving Pressure (18 cmH2O)"', ha='center', va='center', fontsize=7.5, color='#581c87')
    ax.text(88, 6.5, "Zero Extra Blood Draws", ha='center', va='center', fontsize=8, color='#7e22ce', weight='bold')

    plt.tight_layout()
    
    # Save as both high-resolution PNG (300 DPI) and vector SVG
    png_path = "D:/ICU_Mortality_Prediction/research-paper/figures/Figure1_Methodology_Architecture.png"
    svg_path = "D:/ICU_Mortality_Prediction/research-paper/figures/Figure1_Methodology_Architecture.svg"
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Generated:\n  {png_path}\n  {svg_path}")

if __name__ == "__main__":
    create_methodology_diagram()
