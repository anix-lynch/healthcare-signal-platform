# Resume SLA — Healthcare DA (Northstar-Aligned)
# Locked: 2026-04-03
# Owner: Anix Lynch
# Spine coverage: A7 BI Developer (primary) · A4 Analytics Engineer · A1 AI Data Engineer
# Rule: every number traceable to a real file in this repo. "Synthetic" must be said explicitly.

---

## A7 BI Developer — 3 bullets this repo owns

### A7·B1 — Certified DAX Measures in Source Control [Northstar #1 + #8]

**BULLET:**
Code-first Power BI semantic model on Azure Fabric: `Total Revenue` and `Readmission Rate` defined as certified DAX measures in TMDL (source-controlled in git) — business logic lives in code, not in Excel formulas or per-report DAX; consistent numbers for every report that connects to this model (healthcare-da)

**Traceability:**
- `powerbi-model/tables/Patient Encounters.tmdl` L32–44
  - `measure 'Total Revenue' = SUM('Patient Encounters'[TotalCost])` — format: "$#,##0.00"
  - `measure 'Readmission Rate' = DIVIDE(CALCULATE(COUNTROWS(...), ReadmissionFlag=1), COUNTROWS(...))` — format: "0.00%"
- `powerbi-model/relationships.tmdl` — 4 star relationships (Encounters → Patient / Doctor / Hospital / Date)
- `powerbi-model/model.tmdl` — 5 tables defined (Date, Doctor, Hospital, Patient, Patient Encounters)
- `screenshots/healthcare-da-fabric-workspace.png` — Fabric workspace visual proof
- `screenshots/healthcare-da-fabric-lakehouse.png` — Lakehouse with healthcare_encounters table

**Northstar gaps closed:** A7 #1 (✅ upgrade), A7 #8 (✅ upgrade — single star-schema semantic model)
**Stars:** ⭐⭐⭐⭐ (4/5)
**Interview safety:** Say "certified DAX measures in TMDL" not "Power BI dashboard live." The semantic model is defined in code; it connects to Fabric when FABRIC_SERVER env var is set. The TMDL is the proof.

---

### A7·B3 — Domain-Specific DQ Assertions Before Dashboard [Northstar #10]

**BULLET:**
3 clinical-domain SQL assertions in dbt enforce data integrity before encounters reach Power BI: impossible LOS blocked (`assert_no_negative_los`), temporal ordering enforced (`assert_discharge_after_admission`), 30-day readmission window validated (`assert_valid_readmission_logic`) — healthcare business rules as tests, not discovered during dashboard QA (healthcare-da)

**Traceability:**
- `dbt-project/tests/assert_no_negative_los.sql` — `WHERE length_of_stay_days < 0`
- `dbt-project/tests/assert_discharge_after_admission.sql` — temporal ordering check
- `dbt-project/tests/assert_valid_readmission_logic.sql` — `WHERE is_readmission = TRUE AND days_since_last_admission > 30`
- All 3 run against `fact_patient_encounters` via `{{ ref('fact_patient_encounters') }}`

**Northstar gaps closed:** A7 #10 (✅ confirmed with domain specificity), A4 #3 (⚠️ stronger — domain assertions not just generic null checks)
**Stars:** ⭐⭐⭐⭐ (4/5)
**Interview framing:** "These are clinical domain rules that protect the readmission and LOS KPIs in the Power BI model. A generic null check wouldn't catch a negative length of stay — you need to know the domain."

---

### A7·B5 — Full-Stack BI: Raw → dbt → Fabric → Power BI [Northstar #4 + #9]

**BULLET:**
Full-stack BI ownership on Azure Fabric: raw encounter data → dbt star schema (11 models: staging → 2 intermediate → 8 marts) → Fabric Lakehouse → Power BI TMDL — every layer owned without engineering hand-off; replaces manual Excel report preparation with a governed, source-controlled semantic model (healthcare-da, 55,500 synthetic encounters)

**Traceability:**
- `dbt-project/models/staging/stg_healthcare.sql` — raw source → staging
- `dbt-project/models/intermediate/int_encounters_enriched.sql` + `int_readmissions.sql` — business logic layer
- `dbt-project/models/marts/core/` — 8 models: `fact_patient_encounters.sql` + 7 dims (patient, doctor, hospital, date, diagnosis, medication, insurance)
- `powerbi-model/` — TMDL + relationships + tables in git (source-controlled DAX)
- `screenshots/healthcare-da-fabric-lakehouse.png` — Lakehouse with Delta table
- `outputs/02_dbt_proof/dbt_run_results_2026-03-11.json` — `fact_patient_encounters` run: "status: success", 0.93s
- `outputs/03_bi_proof/fabric_lakehouse_proof_2026-03-15.md` — Lakehouse API proof

**Northstar gaps closed:** A7 #4 (✅ confirmed), A7 #9 (✅ confirmed), A4 #7 (⚠️ migration story)
**Stars:** ⭐⭐⭐⭐ (4/5) — full stack confirmed with run logs + screenshots
**Interview safety:** Fabric Lakehouse table (`healthcare_encounters`) has 1,000 sample records loaded via API — not the full 55,500. Say "I provisioned the Fabric Lakehouse via API and loaded a sample for validation; the full dataset runs through dbt locally." FastAPI is Docker-local, not deployed to Azure — say "served locally for dev." The full 55,500 is in the API dataset, not the Fabric table.

---

## A4 Analytics Engineer — seasoning from this repo

### Season into A4·B1 — dbt Model Detail [Northstar A4 #1]
Healthcare-da alone = 11 dbt models with star schema design:
- 1 staging: `stg_healthcare.sql`
- 2 intermediate: `int_encounters_enriched.sql`, `int_readmissions.sql`
- 8 marts: `fact_patient_encounters.sql` + 7 dims
- 3 DQ tests: domain-specific SQL assertions (not generic schema tests)
Fold into A4·B1 as: "star-schema design — staging → intermediate → fact + 7 dim marts — with domain-specific SQL assertions at the mart layer"

---

## A1 AI Data Engineer — MLflow bullet from this repo

### A1·B4 — MLflow End-to-End ML Pipeline [Northstar A1 #5]

**BULLET (existing, still valid):**
End-to-end ML pipeline on Azure Fabric: dbt transformation → XGBoost training (MLflow experiment tracking + artifact registry) → FastAPI serving — full DE and ML lifecycle owned without engineering hand-off (healthcare-da, 55,500 synthetic patient records)

**Traceability:**
- `ml-pipeline/src/train.py` — XGBoost + MLflow + mlflow.xgboost.log_model(...)
- `outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md` — Accuracy: 0.6641, AUC-ROC: 0.5097
- `api/app/main.py` — 11 FastAPI GET endpoints (Swagger proof: `screenshots/healthcare-da-fastapi-docs.png`)

**Interview safety:**
- AUC 0.5097 is barely above random — only cite if asked; show the MLflow log
- Top features: Gender (0.1504), Blood Type (0.1421), Billing Amount (0.1345) — synthetic, not clinical insight
- FastAPI is local/Docker only — NOT deployed to Azure Cloud Run
- Always say "synthetic" or "simulated" data — never claim real hospital outcomes

---

## Northstar gap impact summary (2026-04-03)

| Spine | Was | Now | What changed |
|-------|-----|-----|-------------|
| A7 #1 | ⚠️ | ✅ | TMDL DAX measures confirmed (Total Revenue, Readmission Rate) |
| A7 #8 | ⚠️ | ✅ | Star schema confirmed (7 dims + 1 fact, TMDL in source control) |
| A7 #10 | ✅ | ✅ (stronger) | Clinical-domain SQL assertions, not generic null checks |
| A7 score | 3✅ 2⚠️ 5❌ | 5✅ 0⚠️ 5❌ | Two ⚠️ flipped to ✅ |
| A4 #3 | ⚠️ | ⚠️ (stronger) | Domain assertions give a specific story for "fewer broken dashboards" |
