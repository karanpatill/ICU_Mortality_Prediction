# Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness

**Project Report**  
Submitted in partial fulfillment of the requirements for the course  
**Project (23CSEU7J12)**  

**By:**  
- **Karan Patil** (PRN: 2023025123)  
- **Sarthak Kumbhar** (PRN: 2023025086)  
- **Sumaira Shaik** (PRN: 2023025176)  
- **Krishna Hasare** (PRN: 2023025050)  

**Under the Guidance of:**  
**Mrs. Archana Sawant**  
Assistant Professor, CSE Dept.  

**D Y Patil Education Society (Deemed to be University), Kolhapur**  
**School Of Engineering And Management**  
**Department of Computer Science And Engineering**  
**Academic Year: 2026-27**  

---

## CERTIFICATE

This is to certify that the Project titled **"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness"** is a bonafide work carried out by:
- Karan Patil (PRN: 2023025123)
- Sarthak Kumbhar (PRN: 2023025086)
- Sumaira Shaik (PRN: 2023025176)
- Krishna Hasare (PRN: 2023025050)

Final Year Computer Science And Engineering students, in partial fulfillment of the requirements for the course Project (23CSEU7J12) during the academic year 2026-27. The project work has been carried out under our supervision and guidance.

- **Mrs. Archana Sawant** — Project Guide  
- **Dr. G. V. Otari** — Head of Department, CSE  
- **Dr. A. S. Patil** — Director, DYPSEM  

---

## DECLARATION

We hereby declare that the Project titled **"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness"** submitted to the School of Engineering and Management is a record of original work done by us under the guidance of Mrs. Archana Sawant.

The information and data provided in this report is authentic to the best of our knowledge. This project has not been submitted to any other university or institution for the award of any degree or diploma.

**Group Members:**  
- Karan Patil  
- Sarthak Kumbhar  
- Sumaira Shaik  
- Krishna Hasare  

---

## ACKNOWLEDGEMENT

We would like to express our sincere gratitude to all those who have contributed to the completion of this Project. We are deeply grateful to our project guide, Mrs. Archana Sawant, for her invaluable guidance, continuous support, and encouragement throughout the project. We extend our heartfelt thanks to Dr. G. V. Otari, Head of Department, and the faculty members of the Computer Science & Engineering Department for providing us with the necessary resources and infrastructure. Finally, we thank the School of Engineering and Management for providing us with this opportunity to apply our technical knowledge to real-world healthcare challenges.

---

## ABSTRACT

Laboratory tests in intensive care units are measured at irregular intervals, so the latest recorded value of a test may be many hours old when a prediction is made. This study tested whether adding the time since the last laboratory measurement, called Targeted Laboratory Staleness (TLS), improves in-hospital mortality prediction in adult invasively ventilated ICU patients.

Using MIMIC-IV v3.1, we built landmark cohorts at 24 h (23,427 patients, 3,337 deaths) and 48 h (17,072 patients, 2,914 deaths), including only patients alive at the landmark. L2 logistic regression and LightGBM were trained with and without staleness features for 13 laboratory variables, using a patient-level 80/20 split. Discrimination, calibration and Brier score were assessed on the held-out test set, and Base and TLS models were compared with paired patient-level bootstrap resamples (1,000).

LightGBM with TLS reached an AUROC of 0.8672 at 24 h and 0.8595 at 48 h. At 24 h, staleness improved logistic regression AUROC by 0.0108 (95% CI 0.0042 to 0.0174; p ≤ 0.002) but not LightGBM (+0.0019; p = 0.348). At 48 h, it improved LightGBM AUROC by 0.0089 (95% CI 0.0028 to 0.0151; p = 0.006) but not logistic regression (+0.0052; p = 0.222). A missingness indicator alone did not significantly improve LightGBM at either horizon. Calibration slopes ranged from 0.92 to 1.10 across models and horizons. Decision-curve analysis was performed across threshold probabilities of 0.05 to 0.50 alongside discrimination and calibration.

Staleness therefore gave small, model- and horizon-dependent gains in discrimination, not a universal improvement. The study is single-centre and retrospective, uses an internal holdout, and its p-values were not adjusted for multiple testing.

**Keywords:** ICU mortality prediction; mechanical ventilation; laboratory staleness; irregular sampling; MIMIC-IV; calibration; decision curve analysis.

---

## CHAPTER 1: INTRODUCTION
### 1.1 Background and Clinical Motivation
Invasive mechanical ventilation is one of the most common life-supporting interventions in intensive care units (ICUs). Clinicians must continually balance two risks: keeping a patient on the ventilator too long exposes them to complications such as ventilator-associated pneumonia and barotrauma, while withdrawing support too early risks re-intubation and deterioration. Both decisions rest on a running judgement of how sick the patient is and how that is changing. Mortality risk estimates are one input to that judgement.

In modern ICUs, much of the data behind such judgements is already recorded electronically. The Medical Information Mart for Intensive Care (MIMIC-IV) contains de-identified electronic health records from patients admitted to the Beth Israel Deaconess Medical Center. It makes it possible to study how the timing of measurements, and not only their values, relates to patient outcomes.

### 1.2 Limits of Static Severity Scores
Severity scores such as APACHE II and SOFA summarise a patient's physiology into a single number, typically from the worst values in a fixed window such as the first 24 hours. They were designed for stratification and comparison between populations, not for continuous updating. Structurally, they do not model how a patient's measurements evolve over the stay, nor how recent each measurement is.

### 1.3 The Measurement-Age Problem
In an ICU, different variables are measured at very different rates. Heart rate is recorded many times an hour, whereas a lactate or a bilirubin may be drawn once or twice a day, or not at all. A model built on a snapshot of latest values treats a creatinine drawn 20 hours earlier exactly like a heart rate recorded one minute earlier. We use the term *silent drift* for this situation: the model's input still looks like a current value, but the clinical reality it describes may have changed since it was measured.

A measurement's age is itself informative. A laboratory test that was repeated recently often signals clinical concern, and a long gap may signal stability, or may signal that nobody is looking. Whether this information improves mortality prediction is an empirical question, and it is the question this project addresses.

### 1.4 Aim and Objectives
**Aim:** To test whether explicit per-laboratory staleness features improve in-hospital mortality prediction at fixed landmark times in invasively ventilated adult ICU patients, and to package the analysis as a decision-support prototype for academic demonstration.

**Objectives:**
1. Build a reproducible ventilated-patient cohort from MIMIC-IV v3.1 with an exact cohort flow at two landmarks (24 h and 48 h after ICU admission).
2. Engineer Targeted Laboratory Staleness (TLS) features for 13 laboratory variables, with a conservative sentinel value for laboratories never measured.
3. Compare a transparent baseline (L2-regularised logistic regression) with a nonlinear learner (LightGBM), each with and without staleness features.
4. Evaluate discrimination (AUROC, AUPRC), overall accuracy (Brier score), calibration (slope, intercept, reliability plot) and clinical utility (decision curve analysis), with patient-level bootstrap confidence intervals.
5. Demonstrate the output in a comprehensive Streamlit dashboard using synthetic data.

### 1.5 Prediction Target and Reporting Standard
The prediction target is fixed throughout this report as:
> **In-hospital mortality after the T-hour landmark, among adult invasively ventilated ICU patients who survived to T.**

Here T is 24 or 48 hours after ICU admission. Conditioning on survival to T prevents immortal-time bias, because every patient in the analysed cohort is alive at the moment the prediction is made. This study is reported in accordance with the **TRIPOD+AI** statement for prediction-model studies.

---

## CHAPTER 2: PRESENT PRACTICES AND TECHNOLOGY
### 2.1 Existing System and Analysis
Four practices are commonly used to handle irregularly measured clinical variables in prediction models:
1. **Imputation:** Missing or out-of-window values are replaced with the mean, median, or a model-based estimate.
2. **Forward fill (LOCF):** The most recent value is carried forward until a new one arrives.
3. **Dropping old values:** Values older than a threshold are treated as missing.
4. **Staleness as an extra feature:** The time since the last measurement is added as a model input.

### 2.2 Proposed System
The proposed system, Targeted Laboratory Staleness (TLS), has four elements:
- **Per-laboratory staleness:** For each of 13 laboratory variables, the feature is the time in hours between the last measurement and landmark T.
- **Sentinel for never measured:** Set to $2T$ hours (48 h at T24, 96 h at T48).
- **Vitals preserved without decay:** Seven vital-sign groups are summarized by last, mean, minimum, and maximum values without artificial decay.
- **Landmark design:** Strict evaluation at $T=24\text{ h}$ and $T=48\text{ h}$.

---

## CHAPTER 5: REQUIREMENTS AND FEASIBILITY
### Table 5.1: Requirements Matrix
| Type | Requirement |
|---|---|
| **Functional** | Ingest MIMIC-IV cohort; compute staleness per laboratory at T; train logistic regression and LightGBM; output patient-level risk estimate; produce calibration plot and decision curve. |
| **Non-functional** | Reproducibility (fixed seed 42, logged library versions); leakage prevention (no feature uses data after T); CPU-only inference; interpretability (TreeSHAP). |
| **Data** | MIMIC-IV v3.1 via credentialed PhysioNet access; no patient-identifiable data stored in code repository; synthetic data for public demonstration. |

### Table 5.2: Training and Data-Access Status of Team Members
| Team member | Human-subjects training | PhysioNet credentialing / DUA |
|---|---|---|
| Karan Patil | Completed (CITI) | Received / Active |
| Sarthak Kumbhar | Completed (CITI) | Received / Active |
| Sumaira Shaik | Completed (CITI) | Registered / Active |
| Krishna Hasare | Completed (CITI) | Registered / Active |

---

## CHAPTER 7: IMPLEMENTATION AND CODING
### Table 7.1: Reproducibility Record
| Item | Setting |
|---|---|
| Dataset | MIMIC-IV v3.1 |
| Python | 3.12+ |
| Libraries | LightGBM, scikit-learn, pandas, numpy, statsmodels, joblib |
| Random seed | 42 |
| Bootstrap | 1,000 resamples, patient-level, percentile 95% intervals |
| Class weighting | Disabled; natural prevalence scale (14.2% - 17.1%) |

### Table 7.2: Verified MIMIC-IV Clinical Item Identifiers
| Variable | Item ID | Category | Dictionary Label |
|---|---|---|---|
| Heart rate | 220045 | Vital Sign | Heart Rate |
| Systolic BP | 220179, 220050 | Vital Sign | Non-invasive / Arterial systolic BP |
| Diastolic BP | 220180, 220051 | Vital Sign | Non-invasive / Arterial diastolic BP |
| Mean arterial pressure | 220181, 220052 | Vital Sign | Non-invasive / Arterial mean BP |
| Respiratory rate | 220210 | Vital Sign | Respiratory Rate |
| Oxygen saturation | 220277 | Vital Sign | O2 saturation pulseoxymetry |
| Temperature | 223762, 223761 | Vital Sign | Temperature Celsius / Fahrenheit |
| Lactate | 50813 | Laboratory | Lactate |
| Creatinine | 50912 | Laboratory | Creatinine |
| Blood urea nitrogen | 51006 | Laboratory | Urea Nitrogen |
| White blood cells | 51301 | Laboratory | White Blood Cells |
| Hemoglobin | 51222 | Laboratory | Hemoglobin |
| Platelets | 51265 | Laboratory | Platelet Count |
| Sodium | 50983 | Laboratory | Sodium |
| Potassium | 50971 | Laboratory | Potassium |
| Bicarbonate | 50882 | Laboratory | Bicarbonate |
| Glucose | 50931 | Laboratory | Glucose |
| Bilirubin | 50885 | Laboratory | Bilirubin, Total |
| pH | 50820 | Laboratory | pH |
| Chloride | 50902 | Laboratory | Chloride |
| Invasive ventilation | 225792 | Procedure | Invasive Ventilation |

---

## CHAPTER 8: EXPERIMENTAL RESULTS AND BENCHMARK
### Table 8.2: Cohort Flow at Each Landmark
| Characteristic | T24 | T48 |
|---|---|---|
| Adult ICU stays | 94,458 | 94,458 |
| Patients with qualifying ventilation overlap | 27,614 | 27,614 |
| ICU stays lasting at least horizon T | 25,504 | 18,192 |
| Ventilated by horizon T | 23,572 | 17,180 |
| **Eligible patients surviving to T (Analysed)** | **23,427** | **17,072** |
| In-hospital deaths | 3,337 | 2,914 |
| Mortality prevalence | 14.24% | 17.07% |

### Table 8.3: Discrimination on Held-Out Test Set (95% CI)
| Horizon | Model | AUROC (95% CI) | AUPRC (95% CI) |
|---|---|---|---|
| T24 | Logistic regression | 0.838 [0.821, 0.854] | 0.500 [0.462, 0.540] |
| T24 | LightGBM | **0.867 [0.854, 0.881]** | **0.557 [0.519, 0.596]** |
| T48 | Logistic regression | 0.819 [0.803, 0.837] | 0.531 [0.490, 0.573] |
| T48 | LightGBM | **0.859 [0.845, 0.873]** | **0.586 [0.545, 0.628]** |

### Table 8.4: Calibration on Held-Out Test Set (95% CI)
| Horizon and Model | Brier score | Calibration slope | Calibration intercept |
|---|---|---|---|
| T24, Logistic regression | 0.095 [0.088, 0.101] | 0.938 [0.859, 1.022] | -0.086 [-0.245, 0.070] |
| T24, LightGBM | 0.088 [0.082, 0.094] | 0.917 [0.854, 0.987] | -0.026 [-0.156, 0.101] |
| T48, Logistic regression | 0.109 [0.102, 0.117] | 1.096 [1.007, 1.198] | 0.167 [0.001, 0.341] |
| T48, LightGBM | 0.102 [0.095, 0.109] | 1.055 [0.985, 1.134] | 0.179 [0.029, 0.337] |

### Table 8.5 & 8.6: Paired Bootstrap Differences (TLS Minus Base, B = 1,000)
- **T24 Logistic Regression AUROC:** $+0.0108$ (95% CI: $+0.0042$ to $+0.0174$, $p = 0.0020$, statistically significant).
- **T24 Logistic Regression AUPRC:** $+0.0096$ (95% CI: $+0.0011$ to $+0.0182$, $p = 0.0420$, nominally significant).
- **T48 LightGBM AUROC:** $+0.0089$ (95% CI: $+0.0028$ to $+0.0151$, $p = 0.0060$, statistically significant).

---

## CHAPTER 11: USER MANUAL (STREAMLIT DASHBOARD)

### 11.1 Installation and Execution
The clinical decision support prototype is developed in Python using Streamlit. To run the dashboard locally:

1. **Prerequisites:** Python 3.12+ (64-bit) environment.
2. **Clone / Open Workspace:**
   ```bash
   cd D:\ICU_Mortality_Prediction
   ```
3. **Install Dependencies:**
   ```bash
   pip install streamlit lightgbm scikit-learn pandas numpy plotly statsmodels joblib
   ```
4. **Launch Application:**
   ```bash
   streamlit run dashboard/app.py
   ```
5. **Access Interface:** Open web browser at `http://localhost:8501`.

*Data notice:* The public demonstration uses synthetic patient records conforming to the MIMIC-IV schema. Real MIMIC-IV access requires PhysioNet credentialing; no patient-identifiable data is distributed with this application.

### 11.2 Navigating the Operational Dashboard
The AURA-ICU dashboard interface is divided into six clinical operational workbenches accessible via the left sidebar:

1. **Ventilator Telemetry Console:**
   Displays high-resolution respiratory pressure, flow, and volume waveforms. Computes clinical weaning indicators including driving pressure ($P_{\text{plat}} - \text{PEEP}$) and Rapid Shallow Breathing Index (RSBI).
2. **Clinical Dossiers & AI Inference:**
   Provides an electronic health record summary of the selected ICU patient alongside the real-time mortality risk prediction output by the calibrated LightGBM model.
3. **Central Nursing Station (10 Beds):**
   Ward-level triage interface displaying risk bands (Low, Moderate, High, Critical) across 10 active ICU beds, highlighting beds with stale critical biomarkers.
4. **Diagnostic & Biomarker Monitor:**
   Renders the Targeted Laboratory Staleness heatmap across all 13 monitored laboratory tests, categorized by recency: Fresh ($<6\text{ h}$), Moderate ($6-20\text{ h}$), Stale ($20-48\text{ h}$), and Sentinel ($\ge 48\text{ h}$).
5. **Counterfactual Simulation Lab ("What-If"):**
   Enables clinicians to simulate hypothetical repeat testing. Sliding a stale lab's age to 0 hours recalculates the model's updated mortality risk in real time.
6. **Clinical Specification & Protocol:**
   Houses the complete academic report, study methodology, MIMIC-IV item mappings, statistical metrics, risk analysis, and author affiliations.

---

## CHAPTER 12: BIBLIOGRAPHY
1. E. A. Goligher, N. D. Ferguson, and L. J. Brochard, "Clinical challenges in mechanical ventilation," *The Lancet*, vol. 387, no. 10030, pp. 1856-1866, 2016.
2. A. E. W. Johnson et al., "MIMIC-IV, a freely accessible electronic health record dataset," *Scientific Data*, vol. 10, no. 1, p. 1, 2023.
3. W. A. Knaus, E. A. Draper, D. P. Wagner, and J. E. Zimmerman, "APACHE II: A severity of disease classification system," *Critical Care Medicine*, vol. 13, no. 10, pp. 818-829, 1985.
4. J.-L. Vincent et al., "The SOFA (Sepsis-related Organ Failure Assessment) score to describe organ dysfunction/failure," *Intensive Care Medicine*, vol. 22, no. 7, pp. 707-710, 1996.
5. G. S. Collins et al., "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods," *BMJ*, vol. 385, p. e078378, 2024.
6. G. Ke et al., "LightGBM: A highly efficient gradient boosting decision tree," in *Proc. Advances in Neural Information Processing Systems (NIPS)*, 2017, pp. 3146-3154.
7. A. L. Goldberger et al., "PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals," *Circulation*, vol. 101, no. 23, pp. e215-e220, 2000.
8. I. Silva, G. Moody, D. J. Scott, L. A. Celi, and R. G. Mark, "Predicting in-hospital mortality of ICU patients: The PhysioNet/Computing in Cardiology Challenge 2012," *Computing in Cardiology*, vol. 39, pp. 245-248, 2012.
9. A. J. Vickers and E. B. Elkin, "Decision curve analysis: A novel method for evaluating prediction models," *Medical Decision Making*, vol. 26, no. 6, pp. 565-574, 2006.
10. R. D. Riley et al., "Calculating the sample size required for developing a clinical prediction model," *BMJ*, vol. 368, p. m441, 2020.
