"""Single place for every analysis decision. Changing a value here changes the report."""
SEED = 42
HORIZONS = [24, 48]                 # landmark hours after ICU admission
N_BOOT = 1000                       # patient-level bootstrap resamples
TEST_SIZE = 0.20
VAL_SIZE = 0.20                     # of the training part, for LightGBM early stopping
DCA_THRESHOLDS = [round(0.05 + 0.01 * i, 2) for i in range(46)]   # 0.05 .. 0.50
MIMIC_VERSION = "v3.1"
VENT_ITEMID = 225792                # procedureevents: 'Invasive Ventilation'
USE_CLASS_WEIGHTS = False           # if True, recalibration is applied (see modeling.py)

TARGET_SENTENCE = ("In-hospital mortality after the T-hour landmark, among adult invasively "
                   "ventilated ICU patients who survived to T.")

# chartevents itemids (MIMIC-IV icu module) -> feature name
VITALS = {
    220045: "hr", 220179: "sbp", 220180: "dbp", 220181: "map",
    220050: "sbp", 220051: "dbp", 220052: "map",   # arterial line
    220210: "rr", 220277: "spo2", 223762: "temp_c", 223761: "temp_f",
}
# labevents itemids (MIMIC-IV hosp module) -> feature name (13 labs)
LABS = {
    50813: "lactate", 50912: "creatinine", 51006: "bun", 51301: "wbc",
    51222: "hemoglobin", 51265: "platelets", 50983: "sodium", 50971: "potassium",
    50882: "bicarbonate", 50931: "glucose", 50885: "bilirubin", 50820: "ph",
    50902: "chloride",
}
LAB_NAMES = list(LABS.values())
VITAL_NAMES = ["hr", "sbp", "dbp", "map", "rr", "spo2", "temp_c"]   # temp_f converted into temp_c

# physiologic plausibility ranges; values outside are set to NaN
RANGES = {
    "hr": (0, 300), "sbp": (20, 300), "dbp": (5, 200), "map": (10, 250), "rr": (0, 100),
    "spo2": (30, 100), "temp_c": (25, 45), "lactate": (0, 40), "creatinine": (0, 30),
    "bun": (0, 300), "wbc": (0, 500), "hemoglobin": (1, 25), "platelets": (0, 2000),
    "sodium": (80, 200), "potassium": (1, 12), "bicarbonate": (2, 60), "glucose": (10, 2000),
    "bilirubin": (0, 80), "ph": (6.5, 8.0), "chloride": (50, 160),
}
