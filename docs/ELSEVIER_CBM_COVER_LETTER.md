# Cover Letter to the Editor-in-Chief

**To:**  
The Editor-in-Chief  
*Computers in Biology and Medicine*  
Elsevier Science Ltd.  

**Date:** November 22, 2026  

**Subject:** Submission of Original Research Manuscript: *"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness: A Dual-Cohort Landmark Study on MIMIC-IV"*

Dear Editor-in-Chief,

On behalf of my co-authors, I am pleased to submit our original research manuscript entitled **"Dynamic Mortality Risk Prediction in Mechanically Ventilated Intensive Care Patients via Targeted Laboratory Staleness: A Dual-Cohort Landmark Study on MIMIC-IV"** for consideration for publication as a regular research paper in *Computers in Biology and Medicine*.

### Scientific Context & Novelty
Invasive mechanical ventilation is an essential life-support intervention in intensive care units (ICUs), yet premature extubation or delayed weaning causes severe clinical complications, including ventilator-associated pneumonia (VAP) and re-intubation mortality rates exceeding 40%. Existing clinical acuity scoring systems (e.g., APACHE-II, SAPS-III, SOFA) rely on static 24-hour admission windows, rendering them blind to the subtle multisystem physiological deterioration ("4-Hour Silent Drift") that precedes catastrophic respiratory collapse.

Conventional machine learning approaches for Electronic Health Records (EHRs) typically handle irregularly sampled laboratory values using naive Last Observation Carried Forward (LOCF) or mean imputation, which artificially distorts biological trajectories and ignores the clinical reality of *Missing Not At Random* (MNAR). In critical care, the clinician's decision to order or defer diagnostic testing (e.g., arterial blood gas, serum lactate) carries powerful prognostic information.

In this work, we introduce **Targeted Laboratory Staleness**, an interpretable clinical machine learning framework that explicitly tracks the continuous elapsed time ($\Delta t$) of intermittent laboratory measurements while decoupling them from continuous hemodynamic vitals. 

### Key Contributions & Experimental Findings:
1. **Methodological Rigor & Landmark Isolation:** We establish a prospective landmark evaluation protocol at $T = 12\text{h}$, $24\text{h}$, and $36\text{h}$ post-admission, strictly isolating prospective features from post-landmark outcomes with an interpretable sentinel mechanism ($\Delta t = 2 \times T$) to eliminate target leakage.
2. **Dual-Cohort Empirical Validation:** Our framework is rigorously evaluated across two independent datasets:
   - A discovery cohort from the PhysioNet 2012 Benchmark ($N = 8,116$ mechanically ventilated ICU stays).
   - An external multi-care-unit validation cohort from the latest **MIMIC-IV v3.1** database ($N = 23,367$ mechanically ventilated admissions; $4,019$ in-hospital deaths, $17.20\%$ mortality).
3. **Statistical Superiority:** Prospective landmark evaluation at $T = 24\text{h}$ demonstrated that Targeted Lab Staleness significantly improves predictive discrimination across gradient boosted decision trees, achieving an **AUROC of 0.8559** (paired 1,000-fold patient bootstrap: $p < 0.0001$; $95\%\text{ CI: } [0.118\%, 0.512\%]$ gain), an **AUPRC of 0.5854** ($p = 0.0250$), and superior probability calibration (Brier score: $0.098$).
4. **Bedside Actionability (AURA-ICU):** With sub-5ms CPU inference latency, the model is integrated into a bedside Clinical Decision Support System that dynamically simulates the reduction in predictive uncertainty when stale arterial blood gases are refreshed.

### Why *Computers in Biology and Medicine* is the Ideal Venue:
*Computers in Biology and Medicine* is renowned for publishing high-impact computational and algorithmic advances addressing critical challenges in clinical medicine and healthcare informatics. Given our emphasis on rigorous mathematical formulation, dual-cohort clinical validation on MIMIC-IV, and open-source reproducibility, we believe this manuscript will strongly resonate with your international readership.

### Declarations:
- **Originality:** This manuscript represents original work that has not been published previously and is not under consideration for publication elsewhere.
- **Ethics & Data Access:** Clinical data was derived from the credentialed MIMIC-IV database (PhysioNet) under Institutional Review Board (IRB) approval from Beth Israel Deaconess Medical Center and MIT (PhysioNet Credentialed DUA Compliance).
- **Conflict of Interest:** All authors declare no competing financial or non-financial interests.
- **Author Approval:** All authors (Karan Patil, Sarthak Kumbhar, Sumaira Shaik, and Krishna Hasare) have read and approved the final manuscript.
- **Publication Track:** We choose the standard **Subscription Publishing Model ($0 Author Processing Charge / Free of Cost)**.

Thank you very much for your time and consideration of our work. We look forward to hearing from you following the peer-review process.

Sincerely,

**Karan Patil** *(Corresponding Author)*  
Department of Computer Science and Engineering  
D. Y. Patil School of Engineering and Management (Deemed-to-be-University)  
Kolhapur, Maharashtra 416013, India  
Email: karanpatil82005@gmail.com  

**Co-Authors:**  
- **Sarthak Kumbhar**, Department of Computer Science and Engineering  
- **Sumaira Shaik**, Department of Computer Science and Engineering  
- **Krishna Hasare**, Department of Computer Science and Engineering  
