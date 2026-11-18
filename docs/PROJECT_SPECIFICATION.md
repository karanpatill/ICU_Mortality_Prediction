# Predicting Mortality Risk in Mechanically Ventilated ICU Patients
## Dynamic Clinical Companion for Real-Time Decision Support

---

## 1. Clinical Background & The "4-Hour Silent Drift"
Mechanical ventilation is a vital life-support intervention for acute respiratory failure (ARDS, sepsis-induced lung injury, severe pneumonia, post-operative respiratory failure). Despite its necessity, ventilated patients face in-hospital mortality rates between **30% and 60%**.

### The Current Clinical Problem:
* **Static Scoring Limitations:** Traditional scoring systems (**APACHE II, SAPS III, SOFA**) evaluate patients cross-sectionally at admission. They provide a static number and fail to track the patient's evolving physiological trajectory over time.
* **The "Silent Drift":** In real ICUs, acute decompensation rarely occurs without warning. Warning signs develop concurrently across multiple organ systems over 4 to 6 hours:
  * FiO₂ demand creeping upward (40% $\to$ 60%)
  * Mean Arterial Pressure (MAP) slowly declining
  * Driving Pressure ($\Delta P = P_{\text{plat}} - \text{PEEP}$) widening beyond 15 cmH₂O
  * Serum lactate gradually climbing
  * Urine output dropping below 0.5 mL/kg/h
* Because individual numbers remain within manageable boundaries, busy clinical teams during overnight shifts miss the integrated pattern. When overt collapse occurs, the therapeutic window has closed.

### The Proposed Solution:
A **24/7 background AI companion** that continuously ingests streaming multimodal data, dynamically assesses near-term mortality risk at landmark horizons ($T=12\text{h}, 24\text{h}, 36\text{h}$), and issues proactive, explainable alerts 4–6 hours ahead of catastrophic decompensation.

---

## 2. Ingested Data Modalities

1. **Hemodynamic Vitals (Every 15–60 min):**
   * Heart Rate (HR), SBP, DBP, MAP, SpO₂, Respiratory Rate (RR), Temperature.
2. **Ventilator Parameters:**
   * PEEP, FiO₂, Tidal Volume ($V_t$), Plateau Pressure ($P_{\text{plat}}$), Driving Pressure ($\Delta P$), P/F Ratio ($\text{PaO}_2 / \text{FiO}_2$).
3. **Intermittent Laboratory Biomarkers (Every 6–24 hrs):**
   * Serum Lactate, Creatinine, BUN, Glucose, Electrolytes ($\text{K}^+, \text{Na}^+, \text{Mg}^{2+}, \text{HCO}_3^-$), CBC (WBC, Platelets, HCT), Liver Panel (ALP, ALT, AST, Bilirubin, Albumin), Arterial Blood Gases (pH, $\text{PaCO}_2, \text{PaO}_2$).
4. **Clinical Assessments & Pharmacology:**
   * Glasgow Coma Scale (GCS), Urine Output, Vasopressors (Norepinephrine titration velocity), Sedatives, Neuromuscular Blockers.

---

## 3. Dynamic Bedside Alerting Design
Every alert delivered by the system provides:
1. **Dynamic Risk Score:** (e.g., *"Patient in Bed 7: 24h mortality risk elevated to 58%, up from baseline 30%"*).
2. **Explainable Physiological Drivers:** Top 3 SHAP feature attributions (e.g., *"Primary drivers: FiO2 escalation trend, MAP drift, rising lactate"*).
3. **Actionable Bedside Checklist:** Recommended clinical actions (e.g., *"Consider repeat ABG & lactate in 1–2 hours; reassess driving pressure and PEEP"*).
