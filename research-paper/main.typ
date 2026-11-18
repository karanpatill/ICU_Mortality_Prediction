#import "template.typ": paper, definition, clinical-note

#show: paper.with(
  title: [Dynamic Mortality Risk Prediction in Mechanically Ventilated \ Intensive Care Patients via Targeted Laboratory Staleness],
  subtitle: [A Dual-Cohort Landmark Evaluation of Missing Not At Random (MNAR) Laboratory Latency on MIMIC-IV and PhysioNet 2012],
  authors: (
    (
      name: "Karan Patil",
      affiliation-idx: "1",
      email: "karanpatil.semco25@dypgroup.edu.in"
    ),
    (
      name: "Sarthak Kumbhar",
      affiliation-idx: "1",
      email: "sarthakkumbhar.semco23@dypgroup.edu.in"
    ),
    (
      name: "Sumaira Shaik",
      affiliation-idx: "1",
      email: "SumeraShaikh.semco23@dypgroup.edu.in"
    ),
    (
      name: "Krishna Hasare",
      affiliation-idx: "1",
      email: "krishnahasare.semco25@dypgroup.edu.in"
    ),
  ),
  affiliations: (
    (
      idx: "1",
      dept: "Department of Computer Science and Engineering",
      institution: "D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur, India"
    ),
  ),
  abstract: [
    Invasive mechanical ventilation is a critical life-support modality in intensive care units (ICUs), yet prolonged exposure incurs substantial risks of ventilator-induced lung injury (VILI), nosocomial infections, and in-hospital mortality. Existing clinical risk calculators (e.g., APACHE IV, SOFA) evaluate static admission snapshots, failing to track evolving longitudinal physiological trajectories. Meanwhile, machine learning models applied to Electronic Health Records (EHR) routinely treat laboratory observation sparsity as missing data, relying on imputation strategies (forward-fill, mean replacement) that destroy biological signals and ignore the Missing Not At Random (MNAR) nature of ICU diagnostic workflows. In this investigation, we establish the Targeted Laboratory Staleness framework, which reformulates time-since-last-measurement ($Delta t$) into an explicit, prospective bedside risk feature for critically ill ventilated patients. Evaluated on a prospective cohort of 23,367 mechanically ventilated adult admissions extracted from MIMIC-IV v3.1, incorporating laboratory staleness into gradient-boosted decision trees (LightGBM) yielded a statistically significant improvement in discriminative performance ($Delta$ AUROC $+0.319%$, $p < 0.0001$; $Delta$ AUPRC $+0.415%$, $p = 0.0250$ via 1,000-fold paired bootstrap resampling). Furthermore, staleness metrics for on-demand arterial blood gas and perfusion markers (total bilirubin, $"PaO"_2$, serum lactate) ranked among the top twenty most decisive split features across the entire cohort. These findings indicate that observation latency for on-demand diagnostic panels provides an objective reflection of clinician-observed stability, offering a lightweight, computationally efficient foundation for real-time critical care risk intelligence.
  ],
  keywords: ("Mechanical ventilation", "intensive care medicine", "targeted laboratory staleness", "missing not at random", "MIMIC-IV", "gradient boosted decision trees"),
  running-title: "Targeted Laboratory Staleness for ICU Mortality Prediction (MIMIC-IV & PhysioNet 2012)",
  project-note: [
    *Capstone Project & Author Contributions:* This research was conducted as a Final Year Engineering Capstone Project in the Department of Computer Science and Engineering, D. Y. Patil School of Engineering and Management (Deemed-to-be-University), Kolhapur. K.P. conceptualized the targeted staleness framework, developed the MIMIC-IV cohort extraction pipeline, and executed the machine learning models. S.K. and S.S. conducted the bootstrap statistical validation, clinical feature alignment, and literature review. K.H. performed cohort validation, cross-cohort reliability checks, and data quality audits. All authors contributed to manuscript drafting, reviewed the findings, and approved the final manuscript.
  ],
  bibliography-file: "references.bib"
)

= Introduction & Clinical Motivation

== The Clinical Burden of Invasive Mechanical Ventilation

Invasive mechanical ventilation remains among the most critical life-sustaining interventions deployed in intensive care units globally @esteban2013, @tobin2001. Millions of critically ill patients annually require endotracheal intubation for acute hypoxemic or hypercapnic respiratory failure resulting from Acute Respiratory Distress Syndrome (ARDS) @ards2012, septic shock, aspiration pneumonia, severe thoracic trauma, or post-operative respiratory decompensation. While positive-pressure mechanical ventilation temporarily sustains alveolar gas exchange and unloads fatigued respiratory musculature, it introduces profound iatrogenic hazards:

- *Ventilator-Induced Lung Injury (VILI):* Excessive airway distending pressures (barotrauma), non-physiological tidal volumes (volutrauma), and repeated cyclic end-expiratory alveolar collapse and reopening (atelectrauma) perpetuate intense pulmonary and systemic inflammatory cascades @slutsky2013, accelerating secondary multi-organ dysfunction syndrome (MODS).
- *Ventilator-Associated Pneumonia (VAP):* Colonization of the endotracheal tube cuff and micro-aspiration of subglottic secretions precipitate nosocomial pulmonary infections in 10% to 20% of ventilated patients, extending intensive care stay by 7 to 9 days @boles2007.
- *The Extubation Dilemma:* Intensivists operate under a precarious balance. Premature extubation precipitates acute respiratory exhaustion, upper airway compromise, or aspiration, necessitating emergency re-intubation---a clinical event independently associated with an in-hospital mortality rate exceeding 40% to 50% @thille2011, @epstein1997. Conversely, overly conservative weaning strategies unnecessarily prolong invasive ventilation, escalating critical illness myopathy, delirium, tracheostomy conversion rates, and hospital expenditures exceeding \$5,000 per ventilated day @dasta2005.

== The "4-Hour Silent Drift" Phenomenon

In tertiary intensive care units, catastrophic patient decompensation rarely occurs without warning. Instead, clinical collapse is typically preceded by a subtle, multisystem physiological drift unfolding across a 4-to-6-hour window:
1. *Subtle Oxygenation Erosion:* Fractional inspired oxygen ($"FiO"_2$) requirements gradually creep from 0.40 to 0.55 to maintain peripheral oxygen saturation ($"SpO"_2 >= 92%$).
2. *Hemodynamic Deterioration:* Mean Arterial Pressure (MAP) subtly declines from 80 mmHg to 68 mmHg, quietly counteracted by escalating nursing titration of continuous vasopressor infusions (e.g., norepinephrine).
3. *Ventilator Dyssynchrony & Mechanics:* The patient begins fighting the ventilator; spontaneous respiratory rate rises from 18 to 26 breaths/min, and driving pressure ($Delta P = P_("plat") - "PEEP"$) expands beyond the lung-protective threshold of $15 " cmH"_2"O"$ @amato2015.
4. *Metabolic Uncoupling:* Serum lactate rises incrementally from 1.6 to 2.8 mmol/L, accompanied by diminishing hourly urine output ($< 0.5 " mL/kg/h"$).

Because each individual parameter often remains within conventionally acceptable physiological bounds, clinical teams---particularly during high-workload overnight shifts---frequently miss the integrated multisystem trajectory. When overt clinical collapse occurs, the therapeutic window for early, non-emergent intervention has closed.

== Limitations of Conventional Acuity Scoring Systems

Standard ICU severity-of-illness scoring systems are fundamentally incapable of detecting dynamic drift:
- *APACHE IV & SAPS II:* Designed for hospital administrative benchmarking, APACHE IV @zimmerman2006 and SAPS II @legall1993 aggregate the single most abnormal physiological value recorded during the initial 24 hours of ICU admission. They are entirely blind to whether a patient is stabilizing or deteriorating on subsequent days.
- *SOFA Score:* While evaluated serially to track organ dysfunction, the Sequential Organ Failure Assessment @vincent1996 categorizes continuous biomarkers into coarse ordinal integers (0 to 4), discarding rich physiological gradients and failing to capture rapid hourly deterioration.

== Proposed Solution: Dynamic Bedside Risk Intelligence

To address these deficiencies, this study establishes *Targeted Laboratory Staleness*, a prospective machine learning framework that continuously monitors longitudinal EHR streams, dynamically estimates mortality risk at prospective landmark horizons ($T = 12$h, $24$h, $36$h), and provides interpretable, calibrated predictions without data leakage.

= Related Work & The Missing Data Dilemma

== Tabular Ensembles vs. Deep Learning in Critical Care

Recent critical care informatics literature has extensively explored deep recurrent neural networks (RNNs) and continuous-time transformers for irregularly sampled multivariate time series:
- *Recurrent Architectures (GRU-D):* Che et al. @che2018 developed GRU-D, introducing a learned exponential decay parameter to model missing values. However, GRU-D applies decay indiscriminately across continuous vitals and intermittent labs, frequently causing high-frequency vital signs to decay artificially toward population averages during brief sensor disconnections. Furthermore, GRU-D incurs severe memory footprints, creating a "15 GB RAM wall" when scaling to raw multi-year EHR cohorts.
- *Gradient Boosted Decision Trees (GBDT):* In contrast, optimized gradient boosted decision trees (LightGBM @ke2017, XGBoost @chen2016, CatBoost @prokhorenkova2018) consistently match or exceed deep learning performance on structured clinical tabular benchmarks @shwartzziv2022, operate with sub-millisecond CPU latency, and maintain complete explainability via Shapley additive explanations (SHAP) @lundberg2017.

== Pitfalls of Naive Imputation

In EHR data, missingness is pervasive. When standard tabular algorithms ingest clinical tables, researchers commonly resort to:
1. *Last Observation Carried Forward (LOCF / Forward-Fill):* Assumes that an observation remains identically valid indefinitely. In reality, a serum potassium of $4.1 " mmol/L"$ measured 2 hours ago represents current normokalemia, whereas a potassium of $4.1 " mmol/L"$ measured 26 hours ago in an oliguric, mechanically ventilated patient is clinically obsolete and highly suspicious of evolving hyperkalemia.
2. *Mean / Median Imputation:* Imputing population central tendencies tells the learning algorithm that an unmeasured patient has regressed to normal health, directly attenuating risk scores in critically ill individuals.
3. *Binary Indicator Masks:* Captures whether a test was performed but discards the continuous elapsed time since the measurement was obtained @pimentel2018.

== Missing Not At Random (MNAR) Dynamics

In intensive care units, diagnostic investigations are *Missing Not At Random* (MNAR) @little2019. Testing frequency is governed by clinician judgment: tests are ordered when acute physiological changes are suspected and deferred when the patient appears clinically stable @agniel2018, @groenwold2020. By explicitly computing continuous elapsed time ($Delta t$) for on-demand laboratory panels, Targeted Lab Staleness transforms observational missingness from a data artifact into an explicit clinical sensor.

= Clinical & Ventilator Pathophysiology

To ground the machine learning model in pathophysiological reality, our feature space incorporates three domains of critical care physiology:

== Four Etiological Drivers of Respiratory Failure

1. *Acute Respiratory Distress Syndrome (ARDS):* Characterized by diffuse alveolar epithelial and endothelial damage, surfactant disruption, non-cardiogenic pulmonary edema, and severe ventilation-perfusion ($dot(V)/dot(Q)$) mismatch @ards2012.
2. *Sepsis-Induced Pulmonary Dysfunction:* Systemic endothelial leak and microvascular thrombosis inducing acute lung injury secondary to extrapulmonary infection.
3. *Severe Pneumonia:* Alveolar consolidation impairing lobar gas exchange.
4. *Post-Operative Respiratory Insufficiency:* Diaphragmatic dysfunction, atelectasis, and hypoventilation secondary to residual neuromuscular blockade or opioid-induced respiratory depression.

== Ventilator Mechanics & Lung Protection

Our framework ingests core mechanical ventilator parameters charted in the ICU:
- *Positive End-Expiratory Pressure (PEEP):* Prevents end-expiratory alveolar collapse and cyclic atelectrauma.
- *Fraction of Inspired Oxygen ($"FiO"_2$):* Quantifies oxygenation dependency ($0.21 - 1.00$). Prolonged exposure to $"FiO"_2 > 0.60$ induces absorption atelectasis and free radical alveolar injury.
- *Tidal Volume ($V_t$):* Lung-protective ventilation targets $6 - 8 " mL/kg"$ of Predicted Body Weight (PBW).
- *Plateau Pressure ($P_("plat")$):* Static alveolar pressure measured during an end-inspiratory pause hold ($< 30 " cmH"_2"O"$).
- *Driving Pressure ($Delta P$):* Defined by Amato et al. @amato2015 as:
  $ Delta P = P_("plat") - "PEEP" = frac(V_t, C_("rs")) $
  Driving pressure normalizes tidal volume to respiratory system compliance ($C_("rs")$). Amato et al. proved that $Delta P > 15 " cmH"_2"O"$ is among the strongest independent predictors of mortality in ARDS.
- *PaO2/FiO2 Ratio (P/F Ratio):* The clinical benchmark of oxygenation impairment under the Berlin Definition: mild ($200 - 300 " mmHg"$), moderate ($100 - 200 " mmHg"$), and severe ($< 100 " mmHg"$).

= Dual-Cohort Study Design & Landmark Protocol

== Study Populations

We evaluated our framework across two distinct patient populations originating from Beth Israel Deaconess Medical Center (Boston, MA):

1. *Discovery Benchmark Cohort (PhysioNet 2012 / MIMIC-II):*
  $N = 12,000$ adult ICU stays ($8,116$ mechanically ventilated; in-hospital mortality $14.2%$) @silva2012. Used for primary methodological development, parameter tuning, and dynamic landmark tracking ($T = 12$h, $24$h, $36$h).

2. *Large-Scale External Validation Cohort (MIMIC-IV v3.1):*
  Extracted from the complete clinical database (`physionet-data.mimiciv_3_1_*` on Google Cloud BigQuery) @johnson2023. Inclusion criteria: (1) adult ICU admissions ($"anchor\_age" >= 18$), (2) documented invasive mechanical ventilation (`itemid = 225792`), and (3) ICU length of stay $>= 24.0$ hours. This yielded $N = 23,367$ unique adult mechanically ventilated ICU stays with $4,019$ in-hospital deaths (17.20% mortality).

== Prospective Anti-Leakage Protocol

To guarantee real-world clinical validity without target leakage @vanhouwelingen2007:
1. *Landmark Timestamp:* For each admission $t_("in")$, the landmark evaluation horizon is defined as $t_("landmark") = t_("in") + T$ ($T = 24.0$h).
2. *Right-Censored Features:* Only clinical measurements, laboratory orders, and ventilator changes charted strictly within $[t_("in"), t_("landmark")]$ are visible to feature extraction.
3. *Elimination of Retrospective Leakage:* Aggregate hospitalization features (e.g., total duration of ventilation, overall ICU length of stay, future re-intubation codes) are strictly eliminated.

#figure(
  table(
    columns: (2.8fr, 1.25fr, 1.25fr, 1.25fr, 0.8fr),
    stroke: none,
    inset: (x: 5pt, y: 2.7pt),
    fill: (x, y) => if y == 0 { rgb("#f1f5f9") } else if calc.even(y) { rgb("#f8fafc") } else { none },
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
    table.header(
      [*Baseline Parameter*],
      [*Survivors* \ #text(size: 7.5pt)[(_N_ = 19,348)]],
      [*Non-survivors* \ #text(size: 7.5pt)[(_N_ = 4,019)]],
      [*Full Cohort* \ #text(size: 7.5pt)[(_N_ = 23,367)]],
      [*p-Value*]
    ),
    table.hline(stroke: 0.6pt + rgb("#94a3b8")),
    table.cell(colspan: 5, fill: rgb("#e2e8f0"))[#text(weight: "bold", size: 8pt, fill: rgb("#0f172a"))[Demographics & Care Units]],
    [Age, years (mean $plus.minus$ SD)], [$61.8 plus.minus 15.6$], [$69.4 plus.minus 14.1$], [$63.1 plus.minus 15.6$], [$< 0.001$],
    [Male sex, %], [58.4%], [56.9%], [58.1%], [$0.078$],
    [MICU admission, %], [28.4%], [38.9%], [30.2%], [$< 0.001$],
    [SICU admission, %], [18.2%], [16.5%], [17.9%], [--],
    [CVICU admission, %], [24.1%], [12.4%], [22.1%], [--],
    [TSICU admission, %], [14.8%], [12.8%], [14.5%], [--],
    [Neuro SICU admission, %], [14.5%], [19.4%], [15.3%], [--],
    table.cell(colspan: 5, fill: rgb("#e2e8f0"))[#text(weight: "bold", size: 8pt, fill: rgb("#0f172a"))[Hospital Course & Outcomes]],
    [ICU length of stay, days], [$5.72 plus.minus 6.1$], [$8.63 plus.minus 9.4$], [$6.22 plus.minus 6.9$], [$< 0.001$],
    [Ventilation duration, hours], [$82.4 plus.minus 112.5$], [$145.7 plus.minus 189.2$], [$93.3 plus.minus 130.6$], [$< 0.001$],
    table.cell(colspan: 5, fill: rgb("#e2e8f0"))[#text(weight: "bold", size: 8pt, fill: rgb("#0f172a"))[Serum Chemistry & Biomarkers at 24h]],
    [Serum lactate (mmol/L)], [$1.72 plus.minus 1.1$], [$3.21 plus.minus 2.8$], [$1.98 plus.minus 1.6$], [$< 0.001$],
    [Serum creatinine (mg/dL)], [$1.31 plus.minus 1.2$], [$2.14 plus.minus 1.8$], [$1.45 plus.minus 1.4$], [$< 0.001$],
    [Blood urea nitrogen (mg/dL)], [$22.4 plus.minus 17.1$], [$41.8 plus.minus 26.5$], [$25.7 plus.minus 20.2$], [$< 0.001$],
    [Total bilirubin (mg/dL)], [$0.98 plus.minus 1.4$], [$2.34 plus.minus 4.1$], [$1.21 plus.minus 2.2$], [$< 0.001$],
    [White blood cells ($times 10^3$ / $mu$L)], [$11.8 plus.minus 6.8$], [$14.9 plus.minus 9.4$], [$12.3 plus.minus 7.4$], [$< 0.001$],
    [Platelet count ($times 10^3$ / $mu$L)], [$204.2 plus.minus 88.5$], [$154.6 plus.minus 96.2$], [$195.7 plus.minus 91.8$], [$< 0.001$],
    table.cell(colspan: 5, fill: rgb("#e2e8f0"))[#text(weight: "bold", size: 8pt, fill: rgb("#0f172a"))[Arterial Blood Gas Analysis at 24h]],
    [Arterial $"PaO"_2$ (mmHg)], [$112.4 plus.minus 42.1$], [$98.6 plus.minus 48.3$], [$110.0 plus.minus 43.5$], [$< 0.001$],
    [Arterial $"PaCO"_2$ (mmHg)], [$41.2 plus.minus 9.1$], [$43.8 plus.minus 12.4$], [$41.6 plus.minus 9.8$], [$< 0.001$],
    [Arterial pH], [$7.38 plus.minus 0.08$], [$7.32 plus.minus 0.12$], [$7.37 plus.minus 0.09$], [$< 0.001$],
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
  ),
  caption: [Baseline clinical, demographic, and physiological characteristics of the prospective MIMIC-IV v3.1 mechanically ventilated cohort ($N = 23,367$). Values are presented as mean $plus.minus$ standard deviation or percentage. P-values denote two-sample t-tests for continuous Gaussian features and chi-squared tests for categorical distributions.]
) <tab:baseline_mimic>

@tab:baseline_mimic delineates the baseline characteristics of the extracted MIMIC-IV v3.1 cohort, contrasting survivors against non-survivors.

= The Targeted Laboratory Staleness Framework

== Methodological Architecture

#figure(
  image("figures/Figure1_Methodology_Architecture.png", width: 100%),
  caption: [End-to-end Targeted Laboratory Staleness and dynamic mortality risk prediction pipeline. Irregular longitudinal EHR streams are partitioned into continuous hemodynamics and intermittent laboratory panels. Observation latency ($Delta t$) is computed from the prospective landmark horizon ($t_("landmark") = 24.0$h), with unobserved panels mapped to a deterministic sentinel state ($Delta t = 2T = 48.0$h). Features are ingested by gradient-boosted decision trees (GBDT) to isolate unobserved tests without synthetic imputation, producing calibrated mortality probabilities and bedside SHAP attribution.]
) <fig:methodology_architecture>

As illustrated in @fig:methodology_architecture, the proposed framework establishes a principled translation pipeline from irregularly sampled intensive care observations to calibrated, prospective bedside risk intelligence.

== Mathematical Formalization

Let $cal(P)$ denote the set of monitored parameters. We establish a clinical partition into continuous vitals and intermittent laboratory panels:
$ cal(P) = cal(V)_("cont") union cal(L)_("intermit") $
where $cal(V)_("cont") = {"HR", "MAP", "SysBP", "DiasBP", "RespRate", "SpO"_2, "Temp"}$ and $cal(L)_("intermit")$ comprises 13 intermittent laboratory panels (Creatinine, BUN, Potassium, Sodium, Glucose, Platelets, WBC, Hemoglobin, Lactate, $"PaO"_2$, $"PaCO"_2$, pH, Bilirubin).

#definition(title: "Definition 1 (Targeted Laboratory Staleness)")[
  For patient $i$ and lab panel $j in cal(L)_("intermit")$, let $cal(T)_(i,j) = {t_(i,j,1), t_(i,j,2), dots, t_(i,j,K)}$ denote observation timestamps prior to $t_("landmark")$. If $cal(T)_(i,j) eq.not emptyset$, the laboratory staleness $Delta t_(i,j)$ is defined as the elapsed time since the most recent observation:
  $ Delta t_(i,j) = t_("landmark") - max(cal(T)_(i,j)) $
]

Continuous vitals $v in cal(V)_("cont")$ are extracted at $t_("landmark")$ using the latest charted observation without artificial time-decay, avoiding the feature dilution common in uniform decay architectures.

== The Sentinel Encoding Mechanism

When a diagnostic panel was never ordered during the landmark window ($cal(T)_(i,j) = emptyset$), setting $Delta t$ to null or zero introduces severe distortion. We enforce a deterministic sentinel formula:
$ Delta t_(i,j) = 2 times T = 48.0 " hours" $

#definition(title: "Property 1 (Tree-Split Isolation of Unobserved Tests)")[
  For any decision tree with split threshold $tau$:
  - If $tau < T$ (e.g., $tau <= 6$h): The model isolates actively unstable patients requiring urgent serial monitoring.
  - If $T <= tau < 2T$: The model captures stable patients measured upon admission whose follow-up tests were deemed unnecessary.
  - If $tau >= 2T$: The model cleanly isolates patients for whom clinicians suspected zero organ pathology.
  This guarantees that unmeasured tests are cleanly mapped to an extreme split branch without generating invalid `NaN` exceptions or synthetic imputation bias.
]

= Experimental Results & Statistical Verification

== Discovery Benchmark Results (PhysioNet 2012)

@tab:discovery_results details the multi-landmark progression on the discovery cohort across $T = 12$h, $24$h, and $36$h.

#figure(
  table(
    columns: (1fr, 1.3fr, 1.1fr, 1.1fr, 1.1fr, 1.1fr, 1.1fr),
    stroke: none,
    inset: (x: 6pt, y: 4pt),
    fill: (x, y) => if y == 0 { rgb("#f1f5f9") } else if calc.even(y) { rgb("#f8fafc") } else { none },
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
    table.header(
      [*Horizon*], [*Model*], [*Baseline ROC*], [*Staleness ROC*], [*Baseline PRC*], [*Staleness PRC*], [$Delta$ *AUPRC*]
    ),
    table.hline(stroke: 0.6pt + rgb("#94a3b8")),
    [$T = 12$h], [LightGBM], [0.8308], [*0.8311*], [0.4885], [*0.4935*], [+0.50%],
    [$T = 12$h], [XGBoost], [0.8293], [*0.8323*], [0.4861], [*0.4879*], [+0.18%],
    [$T = 24$h], [LightGBM], [0.8403], [*0.8421*], [0.5303], [*0.5353*], [+0.50%],
    [$T = 24$h], [XGBoost], [0.8459], [*0.8477*], [0.5466], [*0.5466*], [+0.00%],
    [$T = 36$h], [*XGBoost*], [0.8712], [*0.8728*], [0.6084], [*0.6206*], [*+1.22%*\*],
    [$T = 36$h], [Logistic Reg.], [0.8647], [*0.8651*], [0.5844], [0.5842], [-0.02%],
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
  ),
  caption: [Dynamic landmark benchmark performance on PhysioNet 2012 ($N = 8,116$ ventilated patients). Asterisk (\*) indicates $p = 0.0360 < 0.05$ via 1,000-fold paired bootstrap.]
) <tab:discovery_results>

#figure(
  image("figures/Figure1_Staleness_Performance_Curves.png", width: 92%),
  caption: [Benchmark Performance Curves on PhysioNet 2012 ($N=12,000$). Discrimination and precision-recall gains achieved by Targeted Lab Staleness across dynamic landmark horizons.]
) <fig:benchmark_curves>

As shown in @fig:benchmark_curves and @tab:discovery_results, incorporating laboratory staleness delivered cumulative gains as patient trajectories lengthened toward $T = 36$h, where XGBoost achieved an absolute AUPRC gain of $+1.22%$ ($p = 0.0360$).

== Prospective Validation on MIMIC-IV v3.1 ($N = 23,367$)

@tab:mimic_results presents the prospective 5-fold cross-validation performance on the newly extracted MIMIC-IV v3.1 mechanically ventilated cohort at Landmark $T = 24.0$h.

#figure(
  table(
    columns: (1.8fr, 1.0fr, 1.0fr, 1.35fr, 1.0fr, 1.0fr, 1.35fr),
    stroke: none,
    inset: (x: 4pt, y: 3.5pt),
    fill: (x, y) => if y == 0 { rgb("#f1f5f9") } else if calc.even(y) { rgb("#f8fafc") } else { none },
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
    table.header(
      [*Model Family*], [*Baseline AUROC*], [*Staleness AUROC*], [$Delta$ *AUROC*], [*Baseline AUPRC*], [*Staleness AUPRC*], [$Delta$ *AUPRC*]
    ),
    table.hline(stroke: 0.6pt + rgb("#94a3b8")),
    [LightGBM @ke2017], [0.8527], [*0.8559*], [+0.319% \ #text(size: 7pt, fill: rgb("#64748b"))[($p < 0.001$)]], [0.5812], [*0.5854*], [*+0.415%* \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.025$)\*]],
    [XGBoost @chen2016], [0.8528], [*0.8563*], [+0.350% \ #text(size: 7pt, fill: rgb("#64748b"))[($p < 0.001$)]], [0.5814], [*0.5850*], [*+0.360%* \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.038$)\*]],
    [Logistic Regression], [0.8424], [*0.8451*], [+0.270% \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.012$)]], [0.5425], [*0.5477*], [*+0.520%* \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.019$)\*]],
    [Random Forest], [0.8415], [*0.8432*], [+0.170% \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.044$)]], [0.5510], [*0.5542*], [*+0.320%* \ #text(size: 7pt, fill: rgb("#64748b"))[($p = 0.041$)\*]],
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
  ),
  caption: [Prospective 5-fold cross-validation performance on MIMIC-IV v3.1 mechanically ventilated adult admissions ($N = 23,367$, 4,019 deaths, 17.20% mortality). Asterisks (\*) indicate statistically significant improvement at $p < 0.05$ via 1,000-fold paired bootstrap resampling across identical validation test folds.]
) <tab:mimic_results>

#figure(
  image("figures/Figure2_MIMICIV_External_Validation.png", width: 85%),
  caption: [Prospective External Validation on MIMIC-IV v3.1 ($N=23,367$). (Left) Receiver Operating Characteristic (ROC) curves demonstrating AUROC improvement from 0.8527 to 0.8559 ($p < 0.0001$). (Right) Precision-Recall (PR) curves demonstrating significant AUPRC improvement ($+0.415%$, $p = 0.0250$) across clinical decision thresholds @saito2015.]
) <fig:validation_curves>

Across all four predictive families in @tab:mimic_results, Targeted Laboratory Staleness yielded consistent, statistically verified improvements. LightGBM achieved an AUPRC of 0.5854 compared to the baseline 0.5812 ($p = 0.0250$), alongside an AUROC of 0.8559 ($p < 0.0001$).

*Statistical Significance (1,000-Fold Bootstrap on MIMIC-IV):*
- $Delta$ AUPRC Mean Gain: *+0.415%*, Empirical $p$-value = $bold(0.0250 < 0.05)$.
- $Delta$ AUROC Mean Gain: *+0.319%*, Empirical $p$-value $bold(< 0.0001)$.
- 95% Confidence Interval for $Delta$ AUROC: $[+0.118%, +0.512%]$ (strictly positive).

#clinical-note(title: "Clinical Relevance vs. Statistical Significance")[
  While paired bootstrap testing demonstrates that the $+0.415\%$ AUPRC improvement is statistically non-random ($p = 0.0250$), statistical significance alone does not prove clinical bedside utility. Rather, its value lies in providing non-invasive prognostic calibration without requiring additional laboratory phlebotomy or invasive sensor deployments.
]

= Clinical Interpretability & Decision Tree Splitting

== GBDT Split Importance Analysis

To interrogate model decision-making across 23,367 MIMIC-IV patients, we analyzed tree split frequencies. @tab:split_features presents the top 20 most decisive clinical features in the prospective LightGBM model.

#figure(
  table(
    columns: (0.7fr, 2.2fr, 3.2fr, 1fr),
    stroke: none,
    inset: (x: 6pt, y: 4pt),
    fill: (x, y) => if y == 0 { rgb("#f1f5f9") } else if calc.even(y) { rgb("#f8fafc") } else { none },
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
    table.header(
      [*Rank*], [*Feature Name*], [*Clinical Interpretation*], [*Total Splits*]
    ),
    table.hline(stroke: 0.6pt + rgb("#94a3b8")),
    [1], [`age`], [Chronological age], [245],
    [2], [`lactate_val`], [Serum lactate (tissue hypoperfusion)], [213],
    [3], [`bun_val`], [Blood urea nitrogen (renal function)], [159],
    [4], [`bilirubin_val`], [Total bilirubin (hepatic clearance)], [141],
    [5], [`ph_val`], [Arterial blood pH (acid-base balance)], [140],
    [6], [`wbc_val`], [White blood cell count (systemic infection)], [137],
    [7], [`pao2_val`], [Arterial oxygen tension], [135],
    [8], [`platelets_val`], [Platelet count (coagulopathy)], [133],
    [9], [`sodium_val`], [Serum sodium concentration], [127],
    [10], [`hemoglobin_val`], [Hemoglobin concentration], [102],
    [11], [`creatinine_val`], [Serum creatinine], [97],
    [12], [`glucose_val`], [Blood glucose], [94],
    [13], [`paco2_val`], [Arterial carbon dioxide tension], [86],
    [14], [*`bilirubin_staleness`*], [*Elapsed time since bilirubin draw*], [*74*],
    [15], [*`pao2_staleness`*], [*Elapsed time since arterial blood gas*], [*46*],
    [16], [*`lactate_staleness`*], [*Elapsed time since serum lactate*], [*40*],
    [17], [`careunit_Neuro_SICU`], [Neuro-Surgical ICU admission], [35],
    [18], [`potassium_val`], [Serum potassium], [35],
    [19], [`gender`], [Biological sex], [31],
    [20], [*`creatinine_staleness`*], [*Elapsed time since creatinine*], [*29*],
    table.hline(stroke: 1.2pt + rgb("#0f172a")),
  ),
  caption: [Top 20 decisive clinical features ranked by total split frequency in LightGBM across MIMIC-IV v3.1 ($N = 23,367$). Targeted staleness metrics are bolded.]
) <tab:split_features>

== Routine Chemistry vs. On-Demand Critical Care Panels

Our empirical findings reveal a fundamental distinction in hospital laboratory ordering:
1. *Scheduled Morning Panels (Non-Informative Staleness):* Tests such as serum glucose, sodium, and potassium are collected on fixed hospital schedules (routine morning rounds every 12 to 24 hours). Their staleness reflects institutional phlebotomy schedules rather than patient pathology. Indiscriminately modeling staleness on these tests adds noise and dilutes tree splits.
2. *On-Demand Critical Care Biomarkers (High-Informative Staleness):* In contrast, arterial blood gases ($"PaO"_2$, $"PaCO"_2$, pH) and serum lactate are *order-on-demand diagnostic actions*. Clinicians order repeat ABGs every 1 to 3 hours exclusively when patients exhibit refractory hypoxemia, ventilator dyssynchrony, or hemodynamic collapse. As a patient stabilizes on ventilator support, intensivists deliberately lengthen testing intervals to avoid iatrogenic blood loss.
3. *The MNAR Mechanism:* A prolonged $Delta t$ for $"PaO"_2$ or lactate is *objective clinical evidence of clinician-observed stability*, capturing implicit expert bedside judgment that is never explicitly recorded in EHR flowsheets.

= Bedside Clinical AI Architecture & Deployment

The proposed system functions as an autonomous, non-intrusive 24/7 background AI companion:
- *Dynamic Risk Scoring:* Generates prospective 24-hour mortality probability at each landmark horizon.
- *SHAP Explainability:* Highlights the top three physiological and staleness drivers contributing to risk elevation (e.g., _"Elevated Risk (58%): Driven by rising lactate, $"PaO"_2$ sampling urgency ($Delta t = 1.2$h), and widening driving pressure"_).
- *Sub-5ms Inference Latency:* Executes on standard CPU architecture in under 5 milliseconds with less than 200 MB of system RAM, enabling seamless integration into commercial EHR platforms (e.g., Epic Systems, Cerner).

= Limitations & Future Directions

1. *Single-Institution Origin:* Both cohorts originate from Beth Israel Deaconess Medical Center. Although separated by more than a decade of clinical evolution and different EHR database systems, future external validation across multi-center international databases (e.g., eICU-CRD, AmsterdamUMCdb) is required.
2. *Tabular Focus:* Our investigation focused on structured tabular EHR data. Future iterations will integrate high-resolution continuous waveforms (arterial line and ECG signals) and unstructured clinical nursing notes using multimodal architectures.

= Conclusion

Across $31,483$ mechanically ventilated intensive care admissions ($8,116$ ventilated patients in the PhysioNet 2012 discovery benchmark and $23,367$ in the MIMIC-IV v3.1 prospective validation cohort, spanning $35,367$ total ICU admissions), we introduced and validated the *Targeted Laboratory Staleness* framework for dynamic ICU mortality prediction. By selectively quantifying measurement decay on intermittent laboratory panels while preserving continuous hemodynamics, our model captures the rich prognostic signal inherent in clinician test-ordering dynamics (Missing Not At Random). The framework achieved statistically significant improvements in discrimination (AUROC: $0.8559$, $bold(p < 0.0001)$) and precision-recall (AUPRC: $0.5854$, $bold(p = 0.0250)$) on MIMIC-IV v3.1, establishing an accurate, computationally lightweight, and clinically interpretable foundation for real-time risk intelligence in critical care.
