# Pattern 3 — forecast 🔮

> **"how bad will this become later, in numbers 😭"**

This is prognosis / forecasting / regression. NOT retrieval (that's retrieval).
NOT classification (that's classifier). NOT generation (that's generation).

forecast answers three brutal questions per encounter:

```
predicted_los_days        →  "patient นี้จะ camp เตียงกี่วัน 😭"
readmission_30d_risk      →  "ปล่อยกลับแล้วโผล่อีกไหม 💀"
mortality_risk_indicator  →  "death aura meter วันนี้"
```

---

## Why it sits here

Each Layer 2 app needs different numbers off the same patient:

```
apps/er-triage              → uses los + mortality (bed planning + escalation)
apps/ops-capacity-assistant → uses los + readmission (discharge routing)
apps/executive-dashboard    → uses los rollup + readmission rate (KPI)
```

Three apps. One forecaster. That's why forecast lives in `shared/`, not
inside any one app folder.

---

## File map

```
shared/regress/
├── __init__.py            public API (predict_prognosis, CrystalBallOutput)
├── schema.py              Pydantic output contract — what every caller gets
├── baseline.py            honest baseline orchestrator (cohort + proxy + heuristic)
├── los_predictor.py       hierarchical cohort-mean LOS (existing, working)
├── leakage_checks.py      "predicting future with discharge_date = cheat 😭" guards
├── eval.py                RMSE / MAE / MAPE / bias / calibration + segment breakdown
├── train_lightgbm.py      OPTIONAL scaffold — tabular boost when enriched data lands
└── README.md              you are here
```

---

## What's shipped vs what's stub

```
COMPONENT                     STATUS         NOTES
─────────────────────────────────────────────────────────────────────────────
LoS — cohort mean             ✅ shipped     hierarchical, hits 55K corpus
LoS — LightGBM                ⚠️ scaffold    waits on enriched data
Readmission — proxy           ✅ shipped     sigmoid on prior_visits — placeholder
Readmission — trained model   ❌ not built   needs comorbidity + SDoH columns
Mortality — rule-based        ✅ shipped     keyword + (age + condition) heuristic
Mortality — real model        ❌ not built   needs ICU telemetry, vitals trends
Eval harness                  ✅ shipped     RMSE/MAE/MAPE/bias/calibration + segments
Leakage guard                 ✅ shipped     fail-loud on discharge-time fields
```

**Do not claim production-grade prognosis.** The data is a billing registry, not
an EHR. The current scaffold is honest about that.

---

## Why regression ≠ classification (the line that gets confused)

```
CLASSIFICATION
    output: discrete bucket
    error type: confusion matrix, F1, precision/recall
    "is this ESI 1 or ESI 2?"

REGRESSION
    output: continuous number
    error type: RMSE, MAE, bias, calibration
    "how many days will this stay?"

different math · different evals · different failure modes
```

A regression model that systematically over-predicts LOS by 1.5 days
fails differently than a classifier that misroutes 10% of ESI-2 to ESI-3.
The eval harness (`eval.py`) reflects this — bias term + segment slice are
non-negotiable.

---

## Why boosting often beats LLMs on tabular data

Pure tabular regression (numeric + low-cardinality categorical) is the
sweet spot of gradient boosting:

- LightGBM / XGBoost handle missing values natively
- categorical features don't need one-hot
- 55K rows × ~15 features = boosting comfort zone, well under LLM scale
- prompted LLMs hallucinate plausible-looking but uncalibrated point estimates
- LLM cost per row → adds up; boost prediction is microseconds

We use boosting (scaffolded in `train_lightgbm.py`) for the LoS estimator.
We use the LLM (Layer 1 enrichment) to generate synthetic narrative + labels,
not to do live prognosis at inference time.

---

## Data limitations (write this in every interview)

Current Layer 1 dataset:

```
WHAT IT HAS                        WHAT IT'S MISSING
─────────────────────────────────  ─────────────────────────────────
demographics                       real vitals (BP/HR/RR/T/SpO2)
condition (free string)            real labs (discrete tests)
admission type + LOS arithmetic    physician notes / HPI
medication (1 column)              comorbidity / problem list
billing amount                     ICU telemetry trends
test_results (single value)        SDoH (housing, insurance churn)
                                   procedure codes / CPT
                                   ICD-10 codes
```

Layer 1 **enriched** dataset (LLM-augmented, runs via
`layer1-data-backbone/scripts/enrich_clinical_narrative.py`) backfills the
left-side gaps with synthetic CC + HPI + vitals + labs + ESI ground-truth.

When `data_source="registry_v2_enriched"` in the output, forecast is
allowed to lift its confidence cap from `low` to `med`. Until real EHR
ingest exists, the cap stays at `med` — never `high`. By design.

---

## Roadmap (when richer data arrives)

```
NOW (registry_v1)              cohort-mean LOS + proxy readmission + rule mortality
                               confidence cap = low
                               warnings = "limited clinical telemetry"

NEXT (registry_v2_enriched)    LightGBM LOS trained on enriched features
                               readmission proxy refined with comorbidity proxy
                               confidence cap = med

REAL (real EHR ingest)         retrain on real labs/vitals/notes
                               real readmission model (calibrated)
                               real mortality predictor (separate model class)
                               confidence cap = high (governed)
```

---

## Healthcare meaning, MJ side-by-side

Same math, different ghosts:

```
CASE                                CRYSTAL BALL OUTPUT
─────────────────────────────────   ──────────────────────────────────
62yo M, chest pain, ambulance       los: 4.2d · mort: med · readm: 0.31
                                    "prep cards bed, plan 4d, watch bounce"

MJ video "Man in the Mirror live"   view_growth_30d: +12K (analog)
                                    "how big does this get later"
```

It's the same Pattern 3. The output shape is the same. The healthcare
context just makes the numbers carry weight.

---

## Senior architect during hospital chaos — the tone we keep

```
BAD                          GOOD
─────────────────────────    ──────────────────────────────────────────
"probably vibing ✨"         "confidence low due to limited clinical telemetry"
"vibes are giving sepsis"   "mortality indicator high — keyword match in CC,
                              clinical review required"
"AI says 5d let's gooo"     "predicted 5d ± 2.3 cohort_std, n=47, registry_v1"
```

The number can be uncertain. The framing cannot be.

---

## Quick start

```python
from shared.regress.baseline import predict_prognosis

case = {
    "cc": "chest pain",
    "hpi": "62yo M with substernal pressure, 30 min, diaphoresis",
    "arrival": "ambulance",
}
out = predict_prognosis(case, case_id="CASE-104", prior_visits=2)
print(out.model_dump_json(indent=2))
```

Output (truncated):

```json
{
  "pattern": "crystal_ball_prognosis",
  "case_id": "CASE-104",
  "los": {
    "predicted_days": 4.2,
    "bin": "medium",
    "cohort_n": 47,
    "cohort_std": 2.31,
    "source_level": "l1_cond+gender+age+adm"
  },
  "readmission": {
    "risk_30d": 0.31,
    "risk_band": "med",
    "method": "proxy_prior_admission_count"
  },
  "mortality": {
    "indicator": "med",
    "rule_fired": "cancer_age_geq_70",
    "requires_clinical_review": true
  },
  "confidence": "low",
  "warnings": [
    "limited clinical telemetry — no real vitals or labs in current data",
    "readmission risk is a proxy from prior_visits, not a trained model",
    "mortality indicator is rule-based heuristic, not a clinical predictor"
  ],
  "data_source": "registry_v1"
}
```

---

## Cross-references

- 7-pattern map: `../../../README.md`
- Layer 1 enrichment script: `../../../layer1-data-backbone/scripts/enrich_clinical_narrative.py`
- Sibling pattern outputs (retrieval, classifier, etc.): `../retrieval/`, `../classify/`, ...
