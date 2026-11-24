# build_project_report.py
# Generates docs/PROJECT_REPORT.md and docs/PROJECT_REPORT.docx
# Fully responsive diagrams, clickable citations with DOI links, and zero running headers.

import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)
RESULTS_DIR = Path("results")

MD_PATH = DOCS_DIR / "PROJECT_REPORT.md"
DOCX_PATH = DOCS_DIR / "PROJECT_REPORT.docx"

REPORT_MD_CONTENT = """# Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness

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

**D Y Patil Education Society, (Deemed to be University), Kolhapur**  
**School Of Engineering And Management**  
**Department of Computer Science And Engineering**  
**Academic Year: 2026-27**  

---

## CERTIFICATE

This is to certify that the Project titled **"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness"** is a bonafide work carried out by:
- **Karan Patil** (PRN: 2023025123)  
- **Sarthak Kumbhar** (PRN: 2023025086)  
- **Sumaira Shaik** (PRN: 2023025176)  
- **Krishna Hasare** (PRN: 2023025050)  

Final Year Computer Science And Engineering students, in partial fulfillment of the requirements for the course Project (23CSEU7J12) during the academic year 2026-27.  
The project work has been carried out under our supervision and guidance.

| Mrs. Archana Sawant (Project Guide) | External Examiner |
| :--- | :--- |
| **Dr. G. V. Otari** (Head of Department) | **Dr. A. S. Patil** (Director, DYPSEM) |

---

## DECLARATION

We hereby declare that the Project titled **"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness"** submitted to the School of Engineering and Management is a record of original work done by us under the guidance of Mrs. Archana Sawant.

The information and data provided in this report is authentic to the best of our knowledge. This project has not been submitted to any other university or institution for the award of any degree or diploma.

**Group Members:**  
- Karan Patil  
- Sarthak Kumbhar  
- Sumaira Shaik  
- Krishna Hasare  

**Place:** Kolhapur  
**Date:** March 2026  

---

## ACKNOWLEDGEMENT

We would like to express our sincere gratitude to all those who have contributed to the completion of this Project.

We are deeply grateful to our project guide, **Mrs. Archana Sawant**, for her invaluable guidance, continuous support, and encouragement throughout the project. Her expertise and insights have been instrumental in shaping this work.

We extend our heartfelt thanks for the valuable feedback and suggestions during the internal assessments, which helped us improve the quality of our project.

We are thankful to **Dr. G. V. Otari**, Head of Department, and the faculty members of the Computer Science & Engineering Department for providing us with the necessary resources and infrastructure to complete this project.

We also acknowledge the support of our family and friends who encouraged us throughout this journey.

Finally, we thank the School of Engineering and Management for providing us with this opportunity to engage with the community and to apply our technical knowledge in proposing solutions to real-world problems.

**Group Members:**  
Karan Patil  
Sarthak Kumbhar  
Sumaira Shaik  
Krishna Hasare  

---

## ABSTRACT

Laboratory tests in intensive care units are measured at irregular intervals, so the latest recorded value of a test may be many hours old when a prediction is made. This study tested whether adding the time since the last laboratory measurement, called Targeted Laboratory Staleness (TLS), improves in-hospital mortality prediction in adult invasively ventilated ICU patients.

Using MIMIC-IV v3.1, we built landmark cohorts at 24 h (23,427 patients, 3,337 deaths) and 48 h (17,072 patients, 2,914 deaths), including only patients alive at the landmark. L2 logistic regression and LightGBM were trained with and without staleness features for 13 laboratory variables, using a patient-level 80/20 split. Discrimination, calibration and Brier score were assessed on the held-out test set, and Base and TLS models were compared with paired patient-level bootstrap resamples (1,000).

LightGBM with TLS reached an AUROC of 0.8672 at 24 h and 0.8595 at 48 h. At 24 h, staleness improved logistic regression AUROC by 0.0108 (95% CI 0.0042 to 0.0174; p ≤ 0.002) but not LightGBM (+0.0019; p = 0.348). At 48 h, it improved LightGBM AUROC by 0.0089 (95% CI 0.0028 to 0.0151; p = 0.006) but not logistic regression (+0.0052; p = 0.222). A missingness indicator alone did not significantly improve LightGBM at either horizon. Calibration slopes ranged from 0.92 to 1.10 across models and horizons. Decision-curve analysis was performed across threshold probabilities of 0.05 to 0.50 alongside discrimination and calibration.

Staleness therefore gave small, model- and horizon-dependent gains in discrimination, not a universal improvement. The study is single-centre and retrospective, uses an internal holdout, and its p-values were not adjusted for multiple testing.

**Keywords:** ICU mortality prediction; mechanical ventilation; laboratory staleness; irregular sampling; MIMIC-IV; calibration; decision curve analysis.

---

## TABLE OF CONTENTS

| Chapter | Title | Page No. |
| :--- | :--- | :--- |
| **1** | **INTRODUCTION** | 1 |
| 1.1 | Background and Clinical Motivation | 1 |
| 1.2 | Limits of Static Severity Scores | 1 |
| 1.3 | The Measurement-Age Problem | 1 |
| 1.4 | Aim and Objectives | 2 |
| 1.5 | Prediction Target and Reporting Standard | 2 |
| 1.6 | Scope of Claims and Target Journals | 2 |
| 1.7 | Organization of the Report | 3 |
| **2** | **PRESENT PRACTICES AND TECHNOLOGY** | 4 |
| 2.1 | Existing System and Analysis | 4 |
| 2.2 | Problem Statement | 4 |
| 2.3 | Proposed System | 4 |
| **3** | **INFORMATION GATHERING** | 6 |
| 3.1 | Literature Search | 6 |
| 3.2 | Dataset: MIMIC-IV | 6 |
| 3.3 | The PhysioNet 2012 Challenge Dataset | 6 |
| **4** | **PROJECT SCOPE** | 7 |
| 4.1 | In Scope | 7 |
| 4.2 | Out of Scope | 7 |
| 4.3 | Target Population and Intended Users | 7 |
| **5** | **REQUIREMENT ANALYSIS AND FEASIBILITY STUDY** | 8 |
| 5.1 | Requirement Analysis | 8 |
| 5.2 | Outcome Definition and Time Horizon | 8 |
| 5.3 | Sample Size | 8 |
| 5.4 | Feasibility Study | 8 |
| 5.5 | Data Governance and Ethics | 9 |
| **6** | **DESIGN AND PLANNING** | 10 |
| 6.1 | System Design and Analysis | 10 |
| 6.2 | Effort Estimation | 15 |
| **7** | **IMPLEMENTATION AND CODING** | 17 |
| 7.1 | Implementation | 17 |
| 7.2 | Coding | 19 |
| **8** | **TESTING** | 21 |
| 8.1 | Testing Strategies | 21 |
| 8.2 | Test Cases | 21 |
| 8.3 | Experimental Results and Evaluation | 22 |
| 8.4 | Interpretation | 28 |
| 8.5 | Exploratory Analysis Using the PhysioNet 2012 Dataset | 29 |
| 8.6 | Conclusion | 30 |
| **9** | **RISK ANALYSIS** | 32 |
| **10** | **LIMITATION AND FUTURE SCOPE** | 33 |
| 10.1 | Limitations | 33 |
| 10.2 | Future Scope | 33 |
| 10.3 | Pre-specified Versus Exploratory Analysis | 34 |
| **11** | **USER MANUAL** | 35 |
| 11.1 | Installation | 35 |
| 11.2 | Navigating the Dashboard | 35 |
| **12** | **BIBLIOGRAPHY** | 36 |

---

## CHAPTER 1: INTRODUCTION

### 1.1 Background and Clinical Motivation
Invasive mechanical ventilation is one of the most common life-supporting interventions in intensive care units (ICUs). Clinicians must continually balance two risks: keeping a patient on the ventilator too long exposes them to complications such as ventilator-associated pneumonia and barotrauma, while withdrawing support too early risks re-intubation and deterioration [[1]](#ref-1). Both decisions rest on a running judgement of how sick the patient is and how that is changing. Mortality risk estimates are one input to that judgement.

In modern ICUs, much of the data behind such judgements is already recorded electronically. The Medical Information Mart for Intensive Care (MIMIC-IV) contains de-identified electronic health records from patients admitted to the Beth Israel Deaconess Medical Center [[2]](#ref-2). It makes it possible to study how the timing of measurements, and not only their values, relates to patient outcomes.

### 1.2 Limits of Static Severity Scores
Severity scores such as APACHE II [[3]](#ref-3) and SOFA [[4]](#ref-4) summarise a patient's physiology into a single number, typically from the worst values in a fixed window such as the first 24 hours. They were designed for stratification and comparison between populations, not for continuous updating. Structurally, they do not model how a patient's measurements evolve over the stay, nor how recent each measurement is. This report makes that structural point only. It does not claim that these scores perform poorly, because no static-score baseline is run in this work.

### 1.3 The Measurement-Age Problem
In an ICU, different variables are measured at very different rates. Heart rate is recorded many times an hour, whereas a lactate or a bilirubin may be drawn once or twice a day, or not at all. A model built on a snapshot of latest values treats a creatinine drawn 20 hours earlier exactly like a heart rate recorded one minute earlier. We use the term *silent drift* for this situation: the model's input still looks like a current value, but the clinical reality it describes may have changed since it was measured. (This is our own term, not an established one.)

A measurement's age is itself informative. A laboratory test that was repeated recently often signals clinical concern, and a long gap may signal stability, or may signal that nobody is looking. Whether this information improves mortality prediction is an empirical question, and it is the question this project addresses.

### 1.4 Aim and Objectives
**Aim.** To test whether explicit per-laboratory staleness features improve in-hospital mortality prediction at fixed landmark times in invasively ventilated adult ICU patients, and to package the analysis as a decision-support prototype for academic demonstration.

**Objectives:**
1. Build a reproducible ventilated-patient cohort from MIMIC-IV v3.1 with an exact cohort flow at two landmarks (24 h and 48 h after ICU admission).
2. Engineer Targeted Laboratory Staleness (TLS) features for 13 laboratory variables, with a sentinel value for laboratories never measured.
3. Compare a transparent baseline (L2-regularised logistic regression) with a nonlinear learner (LightGBM), each with and without staleness features.
4. Evaluate discrimination (AUROC, AUPRC), overall accuracy (Brier score), calibration (slope, intercept, reliability plot) and clinical utility (decision curve analysis), with patient-level bootstrap confidence intervals.
5. Demonstrate the output in a Streamlit dashboard using synthetic data.

### 1.5 Prediction Target and Reporting Standard
The prediction target is fixed throughout this report as:
> **In-hospital mortality after the T-hour landmark, among adult invasively ventilated ICU patients who survived to T.**

Here T is 24 or 48 hours after ICU admission. Conditioning on survival to T prevents immortal-time bias, because every patient in the analysed cohort is alive at the moment the prediction is made.

This study is reported in accordance with the **TRIPOD+AI** statement for prediction-model studies [[5]](#ref-5).

### 1.6 Scope of Claims and Target Journals
The realistic publication targets for the work are *Computers in Biology and Medicine* (Elsevier), *BMC Medical Informatics and Decision Making* (primary) and *Scientific Reports* (secondary). The work is a single-database, retrospective study with calibration and decision-curve analysis. Higher-tier informatics journals such as the *IEEE Journal of Biomedical and Health Informatics*, the *Journal of Biomedical Informatics* and *JAMIA* usually expect external multi-centre validation, prospective evaluation or substantial methodological novelty. None of these is part of this study, so they are out of scope for this run.

### 1.7 Organization of the Report
Chapter 2 reviews present practice and states the problem. Chapters 3 and 4 describe information gathering and scope. Chapter 5 sets out requirements and feasibility. Chapters 6 to 8 cover design, implementation and testing. Chapter 9 analyses risks, Chapter 10 states limitations and future scope, Chapter 11 is the user manual, and Chapter 12 is the bibliography.

---

## CHAPTER 2: PRESENT PRACTICES AND TECHNOLOGY

### 2.1 Existing System and Analysis
Four practices are commonly used to handle irregularly measured clinical variables in prediction models:
1. **Imputation.** Missing or out-of-window values are replaced with the mean, median, or a model-based estimate. This is simple and widely supported, but it assumes a variable is equally meaningful whatever the age of its last measurement.
2. **Forward fill (last observation carried forward).** The most recent value is carried forward until a new one arrives. It reflects what a clinician sees on a chart, but it hides how old the value is.
3. **Dropping old values.** Values older than a threshold are treated as missing. This introduces a hard cut-off that is usually chosen without clinical justification and discards information.
4. **Staleness as an extra feature.** The time since the last measurement is added as a model input. This is the closest practice to our approach. What it usually lacks is a systematic test of whether it is necessary, and an evaluation with calibration and decision-curve analysis.

None of these approaches is wrong in itself. Each makes an assumption about how measurement age relates to meaning, and that assumption is rarely tested.

### 2.2 Problem Statement
Existing practices do not test whether per-variable staleness information adds predictive value beyond the latest measured values. They are also not usually evaluated beyond discrimination, with calibration and decision-curve analysis, on a ventilated MIMIC-IV cohort with a landmark design. The problem addressed here is to test this question rigorously and report the answer honestly, whether the effect turns out to be large, small or null.

### 2.3 Proposed System
The proposed system, Targeted Laboratory Staleness (TLS), has four elements:
1. **Per-laboratory staleness.** For each of 13 laboratory variables, the feature is the time in hours between the last measurement and the landmark T.
2. **Sentinel for never measured.** If a laboratory was never measured before T, its staleness is set to $2T$ hours, a value larger than any observable gap. This is evaluated against a missing-indicator alternative in an ablation.
3. **Vitals preserved without decay.** Seven vital-sign groups (heart rate, systolic, diastolic and mean arterial pressure, respiratory rate, oxygen saturation and body temperature) are each summarised by their last, mean, minimum and maximum values, as measured, and are not decayed.
4. **Landmark design.** Predictions are made at $T = 24\text{ h}$ and $T = 48\text{ h}$, using only data recorded at or before T.

The system is evaluated with logistic regression and LightGBM [[6]](#ref-6). It does not claim to solve staleness. It claims only to test whether staleness features add predictive value.

---

## CHAPTER 3: INFORMATION GATHERING

### 3.1 Literature Search
The literature search covered PubMed, IEEE Xplore, and Google Scholar, focusing on research published between 2016 and 2025. Search terms included combinations of ICU mortality prediction, clinical outcome prediction, measurement staleness, time since last measurement, irregular sampling, informative missingness, temporal feature engineering, and MIMIC-IV.

Studies were considered eligible if they developed or evaluated ICU mortality prediction models using electronic health record data, particularly data from critical-care settings. Studies that did not address mortality or clinical outcome prediction, or lacked sufficient methodological detail, were excluded. A total of 50 research papers published between 2016 and 2025 were reviewed and considered for the literature review. The selected studies helped establish the research background, identify methodological approaches, and understand the role of temporal information and missing clinical measurements in ICU mortality prediction.

### 3.2 Dataset: MIMIC-IV
The analysis uses MIMIC-IV version 3.1, a de-identified database of admissions to the Beth Israel Deaconess Medical Center [[2]](#ref-2). Access requires PhysioNet credentialing, completion of human-subjects research training and signing of a data use agreement [[7]](#ref-7). The modules used are hosp (patients, admissions, laboratory events) and icu (ICU stays, procedure events, chart events).

Invasive ventilation is identified from the ICU procedure events table using item ID 225792, which was verified against the MIMIC-IV item dictionary. Ventilation intervals were matched to ICU stays by actual temporal overlap within the same patient admission. The laboratory and vital-sign item identifiers are listed in Chapter 7.

### 3.3 The PhysioNet 2012 Challenge Dataset
The PhysioNet/Computing in Cardiology Challenge 2012 dataset [[8]](#ref-8) has a fixed public structure: Set A contains 4,000 ICU records with public outcomes, Sets A and B together contain 8,000 records, and Set C contains 4,000 records with withheld outcomes. This study uses Set A only, for a separate exploratory experiment reported in Section 8.5. The primary analysis uses MIMIC-IV. The two datasets differ in cohort, prediction target and design, so their results are never merged or compared directly.

---

## CHAPTER 4: PROJECT SCOPE

### 4.1 In Scope
- A ventilated adult cohort from MIMIC-IV v3.1.
- Landmark predictions at $T = 24\text{ h}$ and $T = 48\text{ h}$.
- Two models: L2 logistic regression and LightGBM.
- Staleness features for 13 laboratory variables, with a sentinel and a missing-indicator ablation.
- Evaluation by AUROC, AUPRC, Brier score, calibration slope and intercept, reliability plot, and decision curve analysis [[9]](#ref-9).
- A Streamlit decision-support demonstration using synthetic data.
- A separate exploratory experiment on PhysioNet 2012 Set A (Section 8.5), kept apart from the primary analysis.

### 4.2 Out of Scope
The following are explicitly not part of this work, and the report does not describe them as done:
- Multi-centre or external validation.
- Prospective evaluation or deployment.
- Competing-risk analysis (death versus discharge alive).
- Paediatric patients.
- Real-time integration with a hospital electronic health record.
- Any claim that the prototype is ready for bedside use.

### 4.3 Target Population and Intended Users
The target population is adult patients (age 18 or older) receiving invasive mechanical ventilation in an ICU and alive at the landmark time. The intended audience of the prototype is academic: students, researchers and reviewers who want to inspect how staleness features behave. It is not intended for clinicians to use on real patients.

---

## CHAPTER 5: REQUIREMENT ANALYSIS AND FEASIBILITY STUDY

### 5.1 Requirement Analysis
Table 5.1 summarizes the system requirements.

**Table 5.1: Requirements**
| Type | Requirement |
| :--- | :--- |
| **Functional** | Ingest the MIMIC-IV cohort; compute staleness per laboratory at T; train logistic regression and LightGBM; output a patient-level risk estimate; produce a calibration plot and decision curve. |
| **Non-functional** | Reproducibility (fixed seed 42, logged library versions); leakage prevention (no feature may use data after T); CPU-only inference; interpretability (SHAP-based feature importance). |
| **Data** | MIMIC-IV v3.1 via credentialed access; no patient-identifiable data stored in the code repository; synthetic data for the public demonstration. |

### 5.2 Outcome Definition and Time Horizon
The outcome is the in-hospital mortality indicator, defined using the target sentence in Section 1.5. The time zero for each patient is ICU admission, and the landmarks are 24 h and 48 h after it. Patients whose ICU stay is shorter than T, who were not ventilated by T, or who died before T are excluded, and each exclusion is counted in the cohort flow (Table 8.2).

### 5.3 Sample Size
The analysed cohort is 23,427 patients at 24 h with 3,337 deaths, and 17,072 patients at 48 h with 2,914 deaths. The Base feature set has 43 candidate predictors, the TLS and missingness sets 56 each, and the combined set 69. With 56 predictors in the TLS set this gives about 60 events per predictor at 24 h and 52 at 48 h (about 48 and 42 for the 69-predictor combined set), well above the traditional minimum of 10 events per variable [[10]](#ref-10). These counts refer to the final expanded model input columns, not to the number of underlying clinical variables.

### 5.4 Feasibility Study
- **Technical feasibility:** The project uses Python, pandas, scikit-learn and LightGBM, all freely available and running on an ordinary laptop or workstation.
- **Economic feasibility:** The credentialed data is free of charge for approved users, no commercial software is required, and computation is done on local CPUs. The cost is therefore effectively limited to team time.
- **Operational feasibility:** The Streamlit dashboard is a demonstration for academic purposes. In line with the project README, it is NOT intended for direct clinical decision-making.

### 5.5 Data Governance and Ethics
This study used the de-identified MIMIC-IV version 3.1 clinical database, distributed through PhysioNet. Access to the credentialed dataset is subject to PhysioNet credentialing, completion of the required human-subjects research training, and acceptance of the data use agreement. The study is a secondary analysis of existing de-identified clinical records. It involved no direct patient contact, recruitment or clinical intervention, and no patient identifiers were used. No patient-level data is redistributed.

All four members of the research team completed the required human-subjects research training and obtained their corresponding certificates for MIMIC-IV access. The team's training status is summarized in Table 5.2. Institutional review determined that this secondary analysis of de-identified open-source data is exempt from formal institutional review board oversight.

**Table 5.2: Training and Data-Access Status of Team Members**
| Team member | Human-subjects training | PhysioNet credentialing / DUA |
| :--- | :--- | :--- |
| Karan Patil | Completed (CITI Program) | Received / Active |
| Sarthak Kumbhar | Completed (CITI Program) | Received / Active |
| Sumaira Shaik | Completed (CITI Program) | Registered / Active |
| Krishna Hasare | Completed (CITI Program) | Registered / Active |

---

## CHAPTER 6: DESIGN AND PLANNING

### 6.1 System Design and Analysis
The system follows a single sequential pipeline: raw MIMIC-IV tables, cohort filter, landmark eligibility, feature engineering (vital-sign summaries, last laboratory values, staleness, missingness indicators), a patient-level data split, model training and evaluation. No data recorded after the landmark T may enter the feature-engineering stage; this is enforced in code by a leakage guard that rejects events after the horizon. The outcome label, in-hospital mortality after T, is attached only at the data-split stage.

The prototype architecture includes:
- **Data extraction module:** hosp and icu modules ingestion.
- **Cohort selection module:** mechanical ventilation overlap filter.
- **Feature extractor:** $2T$ sentinel encoding and staleness calculation.
- **Model trainer:** L2 Logistic Regression & LightGBM.
- **Evaluator:** Non-parametric bootstrap ($B=1,000$), calibration, DCA.
- **Streamlit CDSS Demonstration:** Multi-workbench operational user interface running on synthetic patient cohorts.

### 6.2 Effort Estimation
Table 6.1 gives the estimated person-hours dedicated to each project phase across the academic year.

**Table 6.1: Estimated Person-Hours per Phase**
| Phase | Approximate Period | Estimated Person-Hours |
| :--- | :--- | :--- |
| Literature review and problem definition | 1 Mar to 15 Apr 2026 | 120 |
| Dataset familiarisation and preparation | 1 Apr to 15 May 2026 | 110 |
| Cohort construction and validation | 1 May to 1 Jul 2026 | 160 |
| Feature engineering and TLS extraction | 15 Jun to 15 Aug 2026 | 150 |
| Model development and validation | 1 Aug to 1 Oct 2026 | 180 |
| Statistical evaluation and interpretation | 15 Sep to 15 Nov 2026 | 140 |
| CDSS Dashboard engineering & integration | 1 Oct to 15 Nov 2026 | 110 |
| Report writing and final review | 1 Nov to 30 Nov 2026 | 90 |
| **Total** | | **1,060** |

---

## CHAPTER 7: IMPLEMENTATION AND CODING

### 7.1 Implementation
#### 7.1.1 Environment and reproducibility
The pipeline was run on MIMIC-IV v3.1 with the settings recorded in Table 7.1. All random operations use a fixed seed, and the library versions, run logs and a single source-of-truth file are saved with the results.

**Table 7.1: Reproducibility Record**
| Item | Recorded setting |
| :--- | :--- |
| Dataset | MIMIC-IV v3.1 |
| Python | 3.12+ |
| NumPy / Pandas | 2.x / 2.x |
| Scikit-learn / LightGBM | 1.x / 4.x |
| Random seed | 42 |
| Bootstrap | 1,000 resamples, patient-level, percentile 95% intervals |
| Class weighting | Disabled; probabilities on the natural-prevalence scale |
| Runtime | T24: 625.8 s; T48: 396.7 s |

#### 7.1.2 Cohort construction
The cohort is built from adult ICU stays (age 18 or older) with an invasive ventilation interval that genuinely overlaps the ICU stay within the same admission. A patient enters the cohort at a landmark if ventilation had started by the landmark, the ICU stay lasted at least T hours, and the patient was alive at T. One qualifying ICU stay is kept per patient.

#### 7.1.3 Feature engineering
All configured clinical item identifiers were verified against the appropriate MIMIC-IV v3.1 dictionary tables (Table 7.2). Vital-sign and ventilation identifiers were checked against `d_items` and laboratory identifiers against `d_labitems`. All 21 configured clinical variables were matched.

**Table 7.2: Verified MIMIC-IV Item Identifiers**
| Variable | Item ID | Category | Dictionary label |
| :--- | :--- | :--- | :--- |
| Heart rate | 220045 | Vital Sign | Heart Rate |
| Systolic blood pressure | 220179, 220050 | Vital Sign | Non-invasive / Arterial systolic BP |
| Diastolic blood pressure | 220180, 220051 | Vital Sign | Non-invasive / Arterial diastolic BP |
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

Only events between ICU admission and the landmark are used. Each of the seven vital-sign groups contributes its last, mean, minimum and maximum values. Each of the 13 laboratory variables contributes three representations: the last value, the time since the last measurement (TLS), and a missingness indicator. The four feature sets compared are listed in Table 7.3.

**Table 7.3: Feature Sets**
| Feature set | Included information |
| :--- | :--- |
| Base | Demographics, vital-sign summaries, last laboratory values (43 predictors) |
| TLS | Base plus laboratory staleness (56 predictors) |
| Missingness | Base plus laboratory missingness indicators (56 predictors) |
| Both | Base plus staleness plus missingness (69 predictors) |

#### 7.1.4 Models and data splitting
Two models are evaluated. Logistic regression uses L2 regularisation (C = 1.0), median imputation, standard scaling and at most 2,000 iterations. LightGBM uses at most 2,000 estimators, a learning rate of 0.03, 31 leaves, at least 50 samples per leaf, early stopping after 100 rounds without improvement, and one CPU thread. A stratified patient-level split gives 80% development data and 20% held-out test data, and 20% of the development data is reserved for validation (Table 7.4). No patient appears in more than one split.

**Table 7.4: Patient-Level Data Split**
| Split | T24 | T48 | Role |
| :--- | :--- | :--- | :--- |
| Training | 14,992 | 10,925 | Model fitting |
| Validation | 3,749 | 2,732 | Early stopping |
| Testing | 4,686 | 3,415 | Final evaluation |

### 7.2 Coding
The core logic is the staleness feature. For a laboratory $j$ with last measurement time $t_j$ (hours after ICU admission) and landmark $T$:
$$s_j = T - t_j \quad (\text{measured at or before } T); \quad s_j = 2T \quad (\text{never measured}) \qquad \text{(Eq. 7.1)}$$

```python
# Production Implementation of Equation 7.1
def compute_targeted_staleness(df_events, landmark_T_hours):
    # Enforce strict leakage guard: reject observations after T
    if (df_events['charttime_hours'] > landmark_T_hours).any():
        raise LeakageError("Observation timestamp exceeds landmark horizon T")
    
    # Calculate time since last observation
    t_last = df_events.groupby(['subject_id', 'itemid'])['charttime_hours'].max().unstack()
    staleness = landmark_T_hours - t_last
    
    # Conservative sentinel imputation for unmeasured biomarkers
    sentinel_value = 2.0 * landmark_T_hours
    staleness = staleness.fillna(sentinel_value)
    return staleness
```

---

## CHAPTER 8: TESTING

### 8.1 Testing Strategies
Testing combined a targeted numerical audit of the extracted features against the raw MIMIC-IV records with a built-in leakage guard. The audit compared saved feature values and staleness calculations for three T24 patients with independently retrieved laboratory records: one with a recent lactate measurement, one with an older lactate measurement, and one with no lactate measurement. Creatinine values and staleness were also checked in the sampled cases. The feature extractor rejects any event after the prediction horizon.

### 8.2 Test Cases
Table 8.1 summarizes the verification test cases executed on the data pipeline.

**Table 8.1: Summary of Test Cases**
| Test ID | Input | Expected Output | Actual Output | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | T24 patient with recent lactate measurement; saved features compared with raw records | Saved last value and staleness equal independently retrieved values | Values matched | **Pass** |
| **TC-02** | T24 patient with older lactate measurement | Saved last value and larger staleness equal raw-record values | Values matched | **Pass** |
| **TC-03** | T24 patient with no lactate measurement | Sentinel staleness ($2T = 48\text{ h}$) and missingness indicator 1 | Matched independent retrieval | **Pass** |
| **TC-04** | Creatinine in sampled T24 cases | Saved values and staleness equal raw-record values | Values matched | **Pass** |
| **TC-05** | Event recorded after the landmark ($t > T$) | Event rejected by leakage guard with LeakageError; feature matrix invariant | LeakageError raised strictly; features identical after audit | **Pass** |

### 8.3 Experimental Results and Evaluation
#### 8.3.1 Cohort flow
Table 8.2 reports the exact cohort attrition flow at each landmark.

**Table 8.2: Cohort Flow at Each Landmark**
| Characteristic | T24 | T48 |
| :--- | :--- | :--- |
| Adult ICU stays | 94,458 | 94,458 |
| Patients with qualifying ventilation overlap | 27,614 | 27,614 |
| ICU stays lasting at least the horizon | 25,504 | 18,192 |
| Ventilated by the horizon | 23,572 | 17,180 |
| **Eligible patients surviving to the horizon** | **23,427** | **17,072** |
| In-hospital deaths in the eligible cohort | 3,337 | 2,914 |
| Mortality prevalence | 14.24% | 17.07% |

#### 8.3.2 Primary model performance
**Table 8.3: Discrimination of the TLS Feature Set on the Held-Out Test Set (95% CI)**
| Horizon | Model | AUROC (95% CI) | AUPRC (95% CI) |
| :--- | :--- | :--- | :--- |
| T24 | Logistic regression | 0.838 [0.821, 0.854] | 0.500 [0.462, 0.540] |
| T24 | LightGBM | **0.867 [0.854, 0.881]** | **0.557 [0.519, 0.596]** |
| T48 | Logistic regression | 0.819 [0.803, 0.837] | 0.531 [0.490, 0.573] |
| T48 | LightGBM | **0.859 [0.845, 0.873]** | **0.586 [0.545, 0.628]** |

The test sets contain 4,686 patients (667 deaths) at T24 and 3,415 patients (583 deaths) at T48. The intervals come from 1,000 patient-level bootstrap resamples. LightGBM achieved higher AUROC and AUPRC than logistic regression at both horizons.

**Table 8.4: Calibration of the TLS Feature Set on the Held-Out Test Set (95% CI)**
| Horizon and model | Brier score | Calibration slope | Intercept |
| :--- | :--- | :--- | :--- |
| T24, logistic regression | 0.095 [0.088, 0.101] | 0.938 [0.859, 1.022] | −0.086 [−0.245, 0.070] |
| T24, LightGBM | 0.088 [0.082, 0.094] | 0.917 [0.854, 0.987] | −0.026 [−0.156, 0.101] |
| T48, logistic regression | 0.109 [0.102, 0.117] | 1.096 [1.007, 1.198] | 0.167 [0.001, 0.341] |
| T48, LightGBM | 0.102 [0.095, 0.109] | 1.055 [0.985, 1.134] | 0.179 [0.029, 0.337] |

#### 8.3.3 Effect of laboratory staleness
**Table 8.5: AUROC With and Without Staleness (TLS Minus Base)**
| Horizon and model | Base | TLS | Difference | p-value | Significance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T24, logistic regression | 0.8267 | 0.8375 | **+0.0108** | **0.0020** | Statistically Significant |
| T24, LightGBM | 0.8653 | 0.8672 | +0.0019 | 0.3477 | Not Significant |
| T48, logistic regression | 0.8143 | 0.8195 | +0.0052 | 0.2218 | Not Significant |
| T48, LightGBM | 0.8506 | 0.8595 | **+0.0089** | **0.0060** | Statistically Significant |

**Table 8.6: AUPRC With and Without Staleness (TLS Minus Base)**
| Horizon and model | Base | TLS | Difference | p-value | Significance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T24, logistic regression | 0.4903 | 0.4999 | **+0.0096** | **0.0420** | Nominally Significant |
| T24, LightGBM | 0.5580 | 0.5567 | −0.0013 | 0.7473 | Not Significant |
| T48, logistic regression | 0.5227 | 0.5307 | +0.0080 | 0.1818 | Not Significant |
| T48, LightGBM | 0.5750 | 0.5864 | +0.0114 | 0.1019 | Not Significant |

#### 8.3.4 Ablation analysis
**Table 8.7: LightGBM AUROC by Feature Set**
| Horizon | Base | TLS | Missingness | Both |
| :--- | :--- | :--- | :--- | :--- |
| T24 | 0.8653 | 0.8672 | 0.8638 | 0.8668 |
| T48 | 0.8506 | 0.8595 | 0.8528 | 0.8599 |

At T24, none of the three feature additions significantly improved LightGBM AUROC over Base. At T48, TLS improved AUROC significantly (p = 0.006), missingness alone did not (p = 0.266), and the combination did (p = 0.008).

### 8.4 Interpretation
The results suggest that the time since a laboratory measurement can carry additional predictive information, but not consistently. Staleness helped logistic regression at T24 and LightGBM at T48, and missingness indicators alone gave no significant LightGBM improvement at either horizon. TreeSHAP feature importance identified `bilirubin_staleness` among the top 5 most important features overall, exceeding several static biochemical values.

### 8.5 Exploratory Analysis Using the PhysioNet 2012 Dataset
An exploratory analysis was performed on Set A of the PhysioNet/CinC 2012 Challenge (3,994 patients, 554 deaths) using global exponential decay ($\tau_g = 24\text{ h}$). Five-fold cross-validation yielded an AUROC of 0.8348 vs 0.8292 baseline (+0.0056 gain). Because $\tau$ was tuned on the same folds, this finding is treated strictly as exploratory and kept separate from the primary MIMIC-IV benchmark.

---

## CHAPTER 9: RISK ANALYSIS

**Table 9.1: Risks and Mitigations**
| Risk | Mitigation |
| :--- | :--- |
| **Data leakage** | A timestamp guard raises an error if any feature uses data after T; a leakage audit injects post-T values and checks that the features do not change. All features are reviewed for any quantity that is only known after the landmark. |
| **Immortal-time bias** | The target is conditional on survival to T, as stated in Section 1.5. |
| **Class imbalance** | AUPRC is reported alongside AUROC. No class weighting is applied, so predicted probabilities stay on the natural prevalence scale. If weights are ever used, recalibration is applied before Brier, calibration and decision-curve analysis. |
| **Overfitting** | Patient-level train, validation and test split; LightGBM early stopping on the validation set; all metrics reported on the untouched test set. |
| **Sentinel overfitting** | Ablation comparing sentinel, missing indicator and both. |
| **Calibration drift** | Calibration slope, intercept and reliability plots reported; decision curves reported. |
| **Small subgroups** | Subgroup results are shown only if there are at least 200 patients and 20 deaths; otherwise they are labelled exploratory. |
| **Reproducibility failure** | Fixed random seed, logged library versions and a single source-of-truth file for every number in the report. |
| **Selective reporting** | The original protocol and any deviations are disclosed in Methods (Section 10.3). |

---

## CHAPTER 10: LIMITATION AND FUTURE SCOPE

### 10.1 Limitations
1. **Single centre:** All data come from one hospital, the Beth Israel Deaconess Medical Center.
2. **Retrospective design:** The study analyses historical records and does not evaluate the model in clinical use.
3. **Single-database evaluation:** There is no external validation on an independent hospital database.
4. **No competing-risk analysis:** Death and discharge alive are not modelled as competing events.
5. **Internal calibration only:** Calibration is reported on a held-out test set from the same database.
6. **Demonstration data:** The dashboard uses synthetic data and has not been clinically validated.
7. **Observational association:** Staleness features may reflect how often clinicians choose to order tests, not only how stale information is. The study measures predictive value, not causal effect.
8. **Multiple comparisons:** Reported p-values are nominal and were not adjusted for multiple testing.

### 10.2 Future Scope
- External validation on eICU-CRD or another independent database.
- A competing-risk formulation using MIMIC-IV death and discharge timestamps.
- Temporal validation across MIMIC-IV admission years.
- A prospective pilot with calibration monitoring.

---

## CHAPTER 11: USER MANUAL

### 11.1 Installation
The AURA-ICU Clinical Decision Support System (CDSS) is developed in Python using the Streamlit framework. It is packaged as an offline, modular, self-contained application.

#### Data Notice
The public demonstration uses synthetic patient records that conform to the MIMIC-IV feature schema. Real MIMIC-IV access requires PhysioNet credentialing, completion of human-subjects training, and acceptance of the Data Use Agreement (DUA). No patient-identifiable data is included in this repository or its demonstration.

#### System Requirements
- **Operating System:** Windows 10/11, Ubuntu 20.04+, or macOS.
- **Python Version:** Python 3.12+ (64-bit).
- **Hardware:** Standard dual-core or quad-core CPU; 4 GB RAM minimum (GPU acceleration is not required; inference runs in $< 1\text{ ms}$ on CPU).

#### Step-by-Step Installation & Launch
1. **Navigate to Repository Root:**
   ```bash
   cd D:\ICU_Mortality_Prediction
   ```
2. **Install Required Python Dependencies:**
   ```bash
   pip install streamlit lightgbm scikit-learn pandas numpy plotly statsmodels joblib
   ```
3. **Launch the CDSS Application:**
   Execute the Streamlit runner from the project root directory:
   ```bash
   streamlit run dashboard/app.py
   ```
4. **Access the Web Interface:**
   The browser will automatically open the local host interface:
   ```
   Local URL: http://localhost:8501
   Network URL: http://<local-ip>:8501
   ```
   *(A live public demonstration is hosted at: `https://karanpatill-icu-mortality-prediction-dashboardapp-q61a23.streamlit.app/`)*

---

### 11.2 Navigating the Dashboard
The AURA-ICU CDSS interface features a responsive healthcare design with clean medical typography. The left sidebar hosts the **Operational Workbench Navigation** allowing clinicians, researchers, and examiners to switch between six dedicated clinical views:

#### Workbench 1: Ventilator Telemetry Console (`ventilator_screen.py`)
- **Primary Function:** Simulates a bedside intensive-care mechanical ventilator interface with live graphical waveforms and respiratory mechanics telemetry.
- **Key Display Elements:**
  - **Live Waveform Plots:** High-frequency, synchronized pressure-time ($P_{\text{aw}}$), flow-time ($\dot{V}$), and volume-time ($V$) respiratory curves rendered using Plotly with responsive container width.
  - **Scalar Mechanics Panel:** Peak Inspiratory Pressure (PIP), Plateau Pressure ($P_{\text{plat}}$), Positive End-Expiratory Pressure (PEEP), Mean Airway Pressure ($P_{\text{mean}}$), Inspiratory Tidal Volume ($V_{\text{ti}}$), Expiratory Tidal Volume ($V_{\text{te}}$), Respiratory Rate, Minute Ventilation ($\dot{V}_{\text{E}}$), Static Compliance ($C_{\text{stat}}$), and Airway Resistance ($R_{\text{aw}}$).
  - **Clinical Weaning Telemetry:** Automatically computes Driving Pressure ($\Delta P = P_{\text{plat}} - \text{PEEP}$, alerting when $> 15\text{ cmH}_2\text{O}$), Rapid Shallow Breathing Index (RSBI = $f / V_t$, alerting when $> 105\text{ breaths/min/L}$), and Expiratory Time Constant ($\tau_e$).
  - **Weaning Status Badges:** Real-time assessment badges indicate whether the patient is clinically eligible for spontaneous breathing trials (SBT).

#### Workbench 2: Clinical Dossiers & AI Inference (`clinical_dossier.py`)
- **Primary Function:** Presents the comprehensive electronic health record of the selected ICU patient alongside real-time mortality risk inference.
- **Key Display Elements:**
  - **Demographics & Admission:** Age, gender, admission category (Surgical, Emergency, Medical), initial care unit (MICU, SICU, CCU, TSICU), and total duration on invasive mechanical ventilation.
  - **Calibrated Risk Gauge:** Displays the predicted in-hospital mortality probability output by the production LightGBM model, accompanied by a 95% bootstrap confidence interval.
  - **4-Tier Clinical Risk Bands:**
    - *Low Risk ($< 15\%$):* Stable; suitable for standard weaning protocols.
    - *Moderate Risk ($15\% - 30\%$):* Elevated risk; close hemodynamic and ventilatory monitoring.
    - *High Risk ($30\% - 60\%$):* Substantial mortality hazard; proactive escalation review.
    - *Critical Risk ($> 60\%$):* Impending failure; urgent multidisciplinary intervention indicated.
  - **Clinical Recommendations:** Rule-based actionable suggestions tailored to the patient's specific biomarker profile.

#### Workbench 3: Central Nursing Station (10 Beds) (`ward_view.py`)
- **Primary Function:** Provides an ICU charge-nurse or ward-level triage dashboard summarizing the status of 10 mechanically ventilated beds simultaneously.
- **Key Display Elements:**
  - **Acuity Triage Grid:** 10 individual bed cards color-coded by acuity risk band.
  - **Priority Sorting:** Sort beds dynamically by highest mortality risk, longest ventilation duration, or greatest number of stale laboratory tests.
  - **Quick Telemetry Badges:** At-a-glance indicators for current ventilator mode (e.g., VCV, PCV, PSV), RSBI weaning status, and count of critical labs older than 20 hours.
  - **Bed Selection:** Clicking any bed card instantly activates that patient across all other workbenches.

#### Workbench 4: Diagnostic & Biomarker Monitor (`patient_monitor.py`)
- **Primary Function:** Visualizes longitudinal vital sign trajectories and the Targeted Laboratory Staleness heatmap across all 13 monitored laboratory biomarkers.
- **Key Display Elements:**
  - **Targeted Laboratory Staleness Heatmap:** Color-coded matrix displaying the recency of every laboratory test:
    - *Fresh ($< 6\text{ h}$):* Cyan — recently drawn; measurement is clinically current.
    - *Moderate ($6\text{ h} - 20\text{ h}$):* Light Cyan — acceptable; routine monitoring.
    - *Stale ($20\text{ h} - 48\text{ h}$):* Amber/Orange — clinically stale; potential silent drift.
    - *Sentinel ($\ge 48\text{ h}$):* Crimson/Rose — never measured or older than 48 hours; assigned maximal uncertainty sentinel value ($2T$).
  - **Biomarker Detail Table:** Lists the absolute latest value, standard reference ranges, exact measurement timestamp, and clinical interpretation.
  - **Vital-Sign Trajectories:** 24-hour trend plots for Mean Arterial Pressure, Heart Rate, SpO2, and Body Temperature with normal clinical reference bands.

#### Workbench 5: Counterfactual Simulation Lab ("What-If") (`whatif_sim.py`)
- **Primary Function:** An interactive exploratory sandbox allowing clinicians to evaluate the impact of repeat laboratory testing on model predictions before ordering tests.
- **Key Display Elements:**
  - **Staleness Sliders:** Clinicians adjust the measurement age of key stale biomarkers (e.g., repeating an arterial blood gas or lactate to reset staleness from 28 hours to 0 hours).
  - **Dynamic Recalibration:** Recomputes the model's predicted mortality risk in real time ($< 1\text{ ms}$).
  - **Risk Delta ($\Delta \text{Risk}$):** Clearly quantifies the reduction in predictive uncertainty, demonstrating how acquiring fresh diagnostic data clarifies patient acuity.

#### Workbench 6: Clinical Specification & Protocol (`documentation.py`)
- **Primary Function:** Complete in-app academic reference housing the project report, formal methodology, statistical tables, and institutional documentation.
- **Key Display Elements:**
  - *Executive Summary Tab:* Theoretical background, silent drift problem, and TLS formulation.
  - *Clinical Methodology & Cohort Tab:* Full MIMIC-IV item identifier dictionary (21 variables), landmark inclusion criteria, and patient-level data partitions.
  - *Benchmark Results & Statistics Tab:* Complete empirical tables (discrimination, calibration slopes, paired bootstrap $p$-values, TreeSHAP feature rankings, and DCA curves).
  - *Risk Analysis & Governance Tab:* Methodological risk matrix, data leakage guard verification, and PhysioNet ethical compliance.
  - *Project Team & Academic Record Tab:* Author credentials, PRNs, institutional emails, guide and leadership details, and target journal specifications.
  - *CDSS User Manual Tab:* Complete system setup, dependency management, and operational instructions.

---

## CHAPTER 12: BIBLIOGRAPHY

<div id="ref-1"></div>

- **[[1]](https://doi.org/10.1016/S0140-6736(16)30177-6)** E. A. Goligher, N. D. Ferguson, and L. J. Brochard, "Clinical challenges in mechanical ventilation," *The Lancet*, vol. 387, no. 10030, pp. 1856-1866, 2016. [DOI Link](https://doi.org/10.1016/S0140-6736(16)30177-6)  

<div id="ref-2"></div>

- **[[2]](https://doi.org/10.1038/s41597-022-01899-x)** A. E. W. Johnson et al., "MIMIC-IV, a freely accessible electronic health record dataset," *Scientific Data*, vol. 10, no. 1, p. 1, 2023. [DOI Link](https://doi.org/10.1038/s41597-022-01899-x)  

<div id="ref-3"></div>

- **[[3]](https://doi.org/10.1097/00003246-198510000-00009)** W. A. Knaus, E. A. Draper, D. P. Wagner, and J. E. Zimmerman, "APACHE II: A severity of disease classification system," *Critical Care Medicine*, vol. 13, no. 10, pp. 818-829, 1985. [DOI Link](https://doi.org/10.1097/00003246-198510000-00009)  

<div id="ref-4"></div>

- **[[4]](https://doi.org/10.1007/BF01709751)** J.-L. Vincent et al., "The SOFA (Sepsis-related Organ Failure Assessment) score to describe organ dysfunction/failure," *Intensive Care Medicine*, vol. 22, no. 7, pp. 707-710, 1996. [DOI Link](https://doi.org/10.1007/BF01709751)  

<div id="ref-5"></div>

- **[[5]](https://doi.org/10.1136/bmj-2023-078378)** G. S. Collins et al., "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods," *BMJ*, vol. 385, p. e078378, 2024. [DOI Link](https://doi.org/10.1136/bmj-2023-078378)  

<div id="ref-6"></div>

- **[[6]](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)** G. Ke et al., "LightGBM: A highly efficient gradient boosting decision tree," in *Proc. Advances in Neural Information Processing Systems (NIPS)*, 2017, pp. 3146-3154. [Paper Link](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html)  

<div id="ref-7"></div>

- **[[7]](https://doi.org/10.1161/01.CIR.101.23.e215)** A. L. Goldberger et al., "PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals," *Circulation*, vol. 101, no. 23, pp. e215-e220, 2000. [DOI Link](https://doi.org/10.1161/01.CIR.101.23.e215)  

<div id="ref-8"></div>

- **[[8]](https://doi.org/10.1109/CIC.2012.6424294)** I. Silva, G. Moody, D. J. Scott, L. A. Celi, and R. G. Mark, "Predicting in-hospital mortality of ICU patients: The PhysioNet/Computing in Cardiology Challenge 2012," *Computing in Cardiology*, vol. 39, pp. 245-248, 2012. [DOI Link](https://doi.org/10.1109/CIC.2012.6424294)  

<div id="ref-9"></div>

- **[[9]](https://doi.org/10.1177/0272989X06295361)** A. J. Vickers and E. B. Elkin, "Decision curve analysis: A novel method for evaluating prediction models," *Medical Decision Making*, vol. 26, no. 6, pp. 565-574, 2006. [DOI Link](https://doi.org/10.1177/0272989X06295361)  

<div id="ref-10"></div>

- **[[10]](https://doi.org/10.1136/bmj.m441)** R. D. Riley et al., "Calculating the sample size required for developing a clinical prediction model," *BMJ*, vol. 368, p. m441, 2020. [DOI Link](https://doi.org/10.1136/bmj.m441)  
"""

def generate_markdown():
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(REPORT_MD_CONTENT)
    print(f"Generated Markdown at {MD_PATH}")

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_hyperlink(paragraph, url, text, color="0284C7", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w", "r")} r:id="{r_id}"/>')
    new_run = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:color w:val="{color}"/>{"<w:u w:val=\"single\"/>" if underline else ""}<w:b/></w:rPr><w:t>{text}</w:t></w:r>')
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def generate_docx():
    doc = docx.Document()
    
    # Page setup: Standard A4 with zero top headers anywhere
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True
        
        # Completely remove all running page headers
        section.header.is_linked_to_previous = False
        for p in section.header.paragraphs:
            p.text = ""
        section.first_page_header.is_linked_to_previous = False
        for p in section.first_page_header.paragraphs:
            p.text = ""

    # Base styling
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # ─── COVER PAGE ───────────────────────────────────────────────────────────
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(12)
    t_run = title_p.add_run("DYNAMIC MORTALITY RISK PREDICTION IN MECHANICALLY VENTILATED INTENSIVE CARE PATIENTS VIA TARGETED LABORATORY STALENESS")
    t_run.bold = True
    t_run.font.size = Pt(18)
    t_run.font.color.rgb = RGBColor(15, 23, 42)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(24)
    s_run = sub_p.add_run("PROJECT REPORT\nSubmitted in partial fulfillment of the requirements for the course\nPROJECT (23CSEU7J12)")
    s_run.font.size = Pt(12)
    s_run.font.color.rgb = RGBColor(71, 85, 105)

    auth_p = doc.add_paragraph()
    auth_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    auth_p.paragraph_format.space_after = Pt(28)
    a_run = auth_p.add_run("By\nKaran Patil (PRN: 2023025123)\nSarthak Kumbhar (PRN: 2023025086)\nSumaira Shaik (PRN: 2023025176)\nKrishna Hasare (PRN: 2023025050)")
    a_run.bold = True
    a_run.font.size = Pt(12)
    a_run.font.color.rgb = RGBColor(30, 41, 59)

    guide_p = doc.add_paragraph()
    guide_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    guide_p.paragraph_format.space_after = Pt(36)
    g_run = guide_p.add_run("Under the Guidance of\nMrs. Archana Sawant\nAssistant Professor, CSE Dept.")
    g_run.font.size = Pt(12)
    g_run.font.color.rgb = RGBColor(51, 65, 85)

    inst_p = doc.add_paragraph()
    inst_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    inst_p.paragraph_format.space_before = Pt(40)
    inst_run = inst_p.add_run("D Y PATIL EDUCATION SOCIETY (DEEMED TO BE UNIVERSITY), KOLHAPUR\nSCHOOL OF ENGINEERING AND MANAGEMENT\nDEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\nACADEMIC YEAR: 2026-27")
    inst_run.bold = True
    inst_run.font.size = Pt(12)
    inst_run.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_page_break()

    # ─── CERTIFICATE ──────────────────────────────────────────────────────────
    h_cert = doc.add_paragraph()
    h_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_cert_run = h_cert.add_run("CERTIFICATE")
    h_cert_run.bold = True
    h_cert_run.font.size = Pt(16)
    h_cert_run.font.color.rgb = RGBColor(15, 23, 42)

    p_cert = doc.add_paragraph(
        "This is to certify that the Project titled \"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness\" "
        "is a bonafide work carried out by Karan Patil (PRN: 2023025123), Sarthak Kumbhar (PRN: 2023025086), Sumaira Shaik (PRN: 2023025176), and Krishna Hasare (PRN: 2023025050), "
        "Final Year Computer Science And Engineering students, in partial fulfillment of the requirements for the course Project (23CSEU7J12) during the academic year 2026-27.\n\n"
        "The project work has been carried out under our supervision and guidance."
    )
    p_cert.paragraph_format.space_after = Pt(48)

    sig_table = doc.add_table(rows=2, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = True
    
    sig_cells = [
        ("Mrs. Archana Sawant\nProject Guide", "External Examiner\nExternal Examiner"),
        ("Dr. G. V. Otari\nHead of Department, CSE", "Dr. A. S. Patil\nDirector, DYPSEM")
    ]
    for row_idx, row in enumerate(sig_cells):
        for col_idx, text in enumerate(row):
            cell = sig_table.cell(row_idx, col_idx)
            cell.text = text
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].paragraph_format.space_after = Pt(28)
            set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

    doc.add_page_break()

    # ─── DECLARATION & ACKNOWLEDGEMENT ────────────────────────────────────────
    h_decl = doc.add_paragraph()
    h_decl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_decl_run = h_decl.add_run("DECLARATION")
    h_decl_run.bold = True
    h_decl_run.font.size = Pt(16)

    doc.add_paragraph(
        "We hereby declare that the Project titled \"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness\" "
        "submitted to the School of Engineering and Management is a record of original work done by us under the guidance of Mrs. Archana Sawant.\n\n"
        "The information and data provided in this report is authentic to the best of our knowledge. This project has not been submitted to any other university or institution for the award of any degree or diploma.\n\n"
        "Group Members:\n"
        "1. Karan Patil (PRN: 2023025123)\n"
        "2. Sarthak Kumbhar (PRN: 2023025086)\n"
        "3. Sumaira Shaik (PRN: 2023025176)\n"
        "4. Krishna Hasare (PRN: 2023025050)\n\n"
        "Place: Kolhapur\n"
        "Date: March 2026"
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    h_ack = doc.add_paragraph()
    h_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_ack_run = h_ack.add_run("ACKNOWLEDGEMENT")
    h_ack_run.bold = True
    h_ack_run.font.size = Pt(16)

    doc.add_paragraph(
        "We would like to express our sincere gratitude to all those who have contributed to the completion of this Project.\n\n"
        "We are deeply grateful to our project guide, Mrs. Archana Sawant, for her invaluable guidance, continuous support, and encouragement throughout the project. Her expertise and insights have been instrumental in shaping this work.\n\n"
        "We extend our heartfelt thanks for the valuable feedback and suggestions during the internal assessments, which helped us improve the quality of our project.\n\n"
        "We are thankful to Dr. G. V. Otari, Head of Department, and the faculty members of the Computer Science & Engineering Department for providing us with the necessary resources and infrastructure to complete this project.\n\n"
        "Finally, we thank the School of Engineering and Management for providing us with this opportunity to apply our technical knowledge in solving real-world problems."
    )

    doc.add_page_break()

    # ─── ABSTRACT ─────────────────────────────────────────────────────────────
    h_abs = doc.add_paragraph()
    h_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h_abs_run = h_abs.add_run("ABSTRACT")
    h_abs_run.bold = True
    h_abs_run.font.size = Pt(16)

    doc.add_paragraph(
        "Laboratory tests in intensive care units are measured at irregular intervals, so the latest recorded value of a test may be many hours old when a prediction is made. This study tested whether adding the time since the last laboratory measurement, called Targeted Laboratory Staleness (TLS), improves in-hospital mortality prediction in adult invasively ventilated ICU patients.\n\n"
        "Using MIMIC-IV v3.1, we built landmark cohorts at 24 h (23,427 patients, 3,337 deaths) and 48 h (17,072 patients, 2,914 deaths), including only patients alive at the landmark. L2 logistic regression and LightGBM were trained with and without staleness features for 13 laboratory variables, using a patient-level 80/20 split. Discrimination, calibration and Brier score were assessed on the held-out test set, and Base and TLS models were compared with paired patient-level bootstrap resamples (1,000).\n\n"
        "LightGBM with TLS reached an AUROC of 0.8672 at 24 h and 0.8595 at 48 h. At 24 h, staleness improved logistic regression AUROC by 0.0108 (95% CI 0.0042 to 0.0174; p ≤ 0.002) but not LightGBM (+0.0019; p = 0.348). At 48 h, it improved LightGBM AUROC by 0.0089 (95% CI 0.0028 to 0.0151; p = 0.006) but not logistic regression (+0.0052; p = 0.222). A missingness indicator alone did not significantly improve LightGBM at either horizon. Calibration slopes ranged from 0.92 to 1.10 across models and horizons. Decision-curve analysis was performed across threshold probabilities of 0.05 to 0.50 alongside discrimination and calibration.\n\n"
        "Staleness therefore gave small, model- and horizon-dependent gains in discrimination, not a universal improvement. The study is single-centre and retrospective, uses an internal holdout, and its p-values were not adjusted for multiple testing.\n\n"
        "Keywords: ICU mortality prediction; mechanical ventilation; laboratory staleness; irregular sampling; MIMIC-IV; calibration; decision curve analysis."
    )

    doc.add_page_break()

    # ─── PARSE REPORT CHAPTERS ────────────────────────────────────────────────
    lines = REPORT_MD_CONTENT.split("\n")
    skip = True

    citation_urls = {
        "[1]": "https://doi.org/10.1016/S0140-6736(16)30177-6",
        "[2]": "https://doi.org/10.1038/s41597-022-01899-x",
        "[3]": "https://doi.org/10.1097/00003246-198510000-00009",
        "[4]": "https://doi.org/10.1007/BF01709751",
        "[5]": "https://doi.org/10.1136/bmj-2023-078378",
        "[6]": "https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html",
        "[7]": "https://doi.org/10.1161/01.CIR.101.23.e215",
        "[8]": "https://doi.org/10.1109/CIC.2012.6424294",
        "[9]": "https://doi.org/10.1177/0272989X06295361",
        "[10]": "https://doi.org/10.1136/bmj.m441"
    }

    def render_paragraph_with_clickable_citations(p, text):
        import re
        tokens = re.split(r'(\[\[\d+\]\]\(#ref-\d+\)|\[\d+\])', text)
        for token in tokens:
            if not token:
                continue
            matched_num = None
            if token.startswith("[[") and "](#ref-" in token:
                m = re.search(r'\[\[(\d+)\]\]', token)
                if m:
                    matched_num = f"[{m.group(1)}]"
            elif re.match(r'^\[\d+\]$', token):
                matched_num = token

            if matched_num and matched_num in citation_urls:
                add_hyperlink(p, citation_urls[matched_num], matched_num)
            else:
                p.add_run(token)

    for line in lines:
        if line.startswith("## CHAPTER 1:"):
            skip = False
        if skip:
            continue
        
        # Headings
        if line.startswith("## CHAPTER "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(18)
            h.paragraph_format.space_after = Pt(8)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(line.replace("## ", ""))
            r.bold = True
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(15, 23, 42)
        elif line.startswith("### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(line.replace("### ", ""))
            r.bold = True
            r.font.size = Pt(12)
            r.font.color.rgb = RGBColor(30, 41, 59)
        elif line.startswith("#### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(line.replace("#### ", ""))
            r.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(51, 65, 85)
        elif line.startswith("```"):
            pass  # omit raw code fences
        elif line.startswith("| ") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) > 1:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.2)
                p.paragraph_format.space_after = Pt(2)
                render_paragraph_with_clickable_citations(p, " •  " + "  |  ".join(cells))
        elif line.startswith("- ") or line.startswith("* "):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            render_paragraph_with_clickable_citations(p, line[2:])
        elif any(line.startswith(f"{i}. ") for i in range(1, 15)):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(2)
            idx_space = line.find(" ")
            render_paragraph_with_clickable_citations(p, line[idx_space+1:])
        elif line.strip() == "" or line.startswith("<div"):
            pass
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            render_paragraph_with_clickable_citations(p, line)

    # Insert verified responsive clinical figures into document at the end of Chapter 8
    img_files = [
        (RESULTS_DIR / "fig_cohort_flow.png", "Figure: Cohort Selection Flow at T=24h and T=48h"),
        (RESULTS_DIR / "fig_roc_T24.png", "Figure: ROC Curves with 95% Confidence Intervals (T=24h)"),
        (RESULTS_DIR / "fig_calibration_T24.png", "Figure: Calibration Reliability Plot (T=24h)"),
        (RESULTS_DIR / "fig_dca_T24.png", "Figure: Decision Curve Analysis (DCA Net Clinical Benefit)"),
        (RESULTS_DIR / "fig_shap_T24.png", "Figure: TreeSHAP Feature Attribution (Top 15 Predictors)")
    ]
    for img_path, caption in img_files:
        if img_path.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(12)
            p_img.paragraph_format.keep_with_next = True
            run_img = p_img.add_run()
            run_img.add_picture(str(img_path), width=Inches(5.4))  # strictly within page margins (never spills out)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(14)
            r_cap = p_cap.add_run(caption)
            r_cap.font.size = Pt(9.5)
            r_cap.font.italic = True
            r_cap.font.color.rgb = RGBColor(100, 116, 139)

    doc.save(DOCX_PATH)
    print(f"Generated DOCX at {DOCX_PATH}")

if __name__ == "__main__":
    generate_markdown()
    generate_docx()
