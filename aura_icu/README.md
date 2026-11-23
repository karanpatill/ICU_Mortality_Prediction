# AURA-ICU / TLS: rerun pipeline

Regenerates every number, table and figure for the final report from MIMIC-IV v3.1.

## Run (on the machine that holds your credentialed MIMIC-IV files)
```
pip install -r requirements.txt
python run_tests.py --out results/table_tests.csv            # Chapter 8 (all rows must Pass)
python -m aura.run_all --data /path/to/mimiciv --out results  # 1,000 patient-level bootstrap resamples
python make_tables.py --results results                       # report tables from source_of_truth.json
```
`--data` must contain `hosp/` (patients, admissions, labevents) and `icu/` (icustays, procedureevents, chartevents), `.csv` or `.csv.gz`.
`chartevents` and `labevents` are streamed in 5M-row chunks; expect tens of minutes and a few GB RAM.

## Outputs (in `results/`)
`source_of_truth.json` (the only place report numbers come from), `run_log.json` (versions, seed, SHA-256 of the truth file),
`table_metrics.csv`, `table_delta.csv`, `table_ablation.csv`, `table_flow.csv`, `table_tests.csv`,
`fig_cohort_flow.png`, `fig_roc_T*.png`, `fig_calibration_T*.png`, `fig_dca_T*.png`, `fig_shap_T*.png`, `shap_importance_T*.csv`,
`features_T*.csv.gz`, `models_T*.joblib`.

## Locked design (edit only in `aura/config.py`)
Target: *In-hospital mortality after the T-hour landmark, among adult invasively ventilated ICU patients who survived to T.* (Option A)
Horizons 24 h and 48 h from ICU admission; models L2 logistic regression and LightGBM; seed 42; no class weights
(probabilities are on the natural prevalence scale; if you set `USE_CLASS_WEIGHTS=True`, Platt recalibration is applied before Brier, calibration and DCA).

## Analysis choices to state in Methods (decide if you disagree, then change the code)
1. Unit = patient: the first invasively ventilated ICU stay per patient (no patient in two splits).
2. "Ventilated" = invasive ventilation (itemid 225792) started on or before T. This avoids using future information to define the cohort. It adds a flow step.
3. Alive at T = no `deathtime` on or before ICU admission + T. ICU LOS must be >= T.
4. Features use only events in [0, T] hours after ICU admission (hard `assert_no_leakage` guard). Labs are matched by `hadm_id`.
5. Staleness = T - t_last (hours); never measured -> 2*T. Vitals: last/mean/min/max, no decay.
6. Split: 80/20 stratified holdout test; 20% of training used only for LightGBM early stopping. All metrics are on the test set.
7. Bootstrap: 1,000 patient-level resamples of the test set, percentile 95% CIs, same resamples for every model (paired).
8. Delta = TLS feature set minus no-staleness feature set, same model; p = two-sided bootstrap p (floored at 1/(B+1)).
9. Calibration slope/intercept = logistic regression of outcome on logit(p), reported with bootstrap CIs.
10. "SHAP" figures use LightGBM's built-in TreeSHAP (`pred_contrib=True`), no extra package.

## Verify before you trust the output
Itemids were written from memory of the MIMIC-IV dictionary. Check every one against `d_items` / `d_labitems`
(vitals and 225792 ventilation in `icu/d_items`, labs in `hosp/d_labitems`) and edit `config.py` if any differ.
The synthetic generator (`aura/synthetic.py`) exists only to test the code. Never report numbers from it.
