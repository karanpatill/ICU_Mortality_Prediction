# AURA-ICU: ICU Mortality Prediction via Targeted Laboratory Staleness

> **Final Year B.E. Capstone Project**  
> D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aura-icu.streamlit.app)
[![medRxiv](https://img.shields.io/badge/medRxiv-Preprint-blue)](https://www.medrxiv.org)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![LightGBM](https://img.shields.io/badge/Model-LightGBM-green)](https://lightgbm.readthedocs.io)

---

## Project Overview

**AURA-ICU** (Adaptive Uncertainty-Aware Risk Assessment for ICU) is an interactive Clinical Decision Support System (CDSS) that predicts 24-hour ICU mortality for mechanically ventilated patients using a novel **Targeted Laboratory Staleness (TLS)** framework.

### The Core Innovation

Standard ML models treat a creatinine value measured 2 hours ago the same as one measured 40 hours ago — this is clinically incorrect. We explicitly encode **how stale** each lab measurement is as a feature, allowing the model to quantify uncertainty from measurement recency.

| Metric | Baseline (Values Only) | **TLS Model** | Improvement |
|--------|----------------------|----------------|-------------|
| AUROC  | 0.8527 | **0.8559** | +0.319% |
| AUPRC  | 0.5812 | **0.5854** | +0.415% |
| p-value | — | **< 0.0001** | Significant |

---

## Live Demo

**Try it here:** [aura-icu.streamlit.app](https://aura-icu.streamlit.app)

> **Note:** The live demo uses **synthetic data** (2,000 simulated patients) that matches the statistical properties of MIMIC-IV. Real MIMIC-IV data requires a PhysioNet Data Use Agreement and cannot be publicly shared.

---

## Dashboard Features

| Tab | Description |
|-----|-------------|
| **Virtual ICU Ward** | 12-bed grid with real-time risk gauges and staleness dot indicators |
| **Patient Monitor** | Full mortality gauge, lab staleness heatmap (13 labs), feature importance |
| **What-If Simulator** | Adjust lab values/staleness with sliders — see risk change instantly |
| **Documentation** | Full methodology, model details, team info |

### Staleness Classification
| Level | Hours | Clinical Meaning |
|-------|-------|-----------------|
| Fresh | < 6h | Current and reliable |
| Moderate | 6-20h | Acceptable, monitor |
| Stale | 20-48h | Clinically questionable |
| Sentinel | >= 48h | No recent data — high uncertainty |

---

## Repository Structure

```
ICU_Mortality_Prediction/
├── dashboard/
│   ├── app.py                    # Main Streamlit application
│   ├── assets/style.css          # Dark hospital theme
│   └── components/
│       ├── utils.py              # Data loading, model inference
│       ├── ward_view.py          # 12-bed ICU ward grid
│       ├── patient_monitor.py    # Patient deep-dive + charts
│       ├── whatif_sim.py         # Clinical What-If simulator
│       └── documentation.py     # Project documentation tab
├── models/
│   ├── lightgbm_staleness_production.joblib   # Trained model
│   └── feature_schema.json                    # Feature metadata + metrics
├── data/
│   └── demo/demo_cohort.csv      # Synthetic demo data (safe to share)
├── research-paper/
│   ├── main.typ                  # Typst source
│   └── output/research-paper.pdf # Compiled 10-page paper
├── experiments/                  # Benchmark scripts
├── scripts/                      # Utility scripts
├── requirements.txt
├── run_dashboard.bat             # Windows one-click launcher
└── ICU_Mortality_Prediction_Master_Pipeline.ipynb
```

---

## Setup & Run (Local)

### Prerequisites
- Python 3.10+

### Installation
```bash
git clone https://github.com/YOUR_USERNAME/ICU_Mortality_Prediction.git
cd ICU_Mortality_Prediction
pip install -r requirements.txt
```

### Run Dashboard
```bash
# Windows (double-click):
run_dashboard.bat

# Or via command line:
streamlit run dashboard/app.py
```

### Using Real MIMIC-IV Data (PhysioNet Access Required)
1. Apply at [physionet.org/content/mimiciv/](https://physionet.org/content/mimiciv/)
2. Place `mimiciv_ventilated_cohort_24h.csv` in `data/mimiciv/`
3. Dashboard auto-detects and uses real data if present

---

## Research Paper

**Title:** Targeted Laboratory Staleness as a Mortality Predictor in Mechanically Ventilated ICU Patients: A MIMIC-IV Analysis

**Preprint:** medRxiv (November 2026)

**Authors:** Karan Patil, Sarthak Kumbhar, Sumaira Shaik, Krishna Hasare  
**Institution:** D. Y. Patil School of Engineering and Management, Kolhapur

---

## Ethical Statement

> This project uses the de-identified MIMIC-IV database (PhysioNet). The live demo uses only synthetic data. This system is built for **academic demonstration purposes only** and is **NOT intended for direct clinical decision-making**.

---

*D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur — B.E. Capstone Project 2026*
