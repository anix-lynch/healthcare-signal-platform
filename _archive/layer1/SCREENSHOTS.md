# Healthcare Analytics - Resume Proof Screenshots

**Purpose:** Visual evidence for each resume bullet claim.

**How these files are produced:** Run `python3 scripts/render_proof_screenshots.py` to regenerate PNGs from `outputs/` proof JSON and Markdown (and `openapi.json` when the API is running). Fabric rows are **text summaries** of validation output; swap in true browser captures of Fabric / Power BI when you want pixel-perfect UI shots.

---

## 1. 55,500 Encounters + 6 Clinical Conditions

**Bullet:** "Built an end-to-end healthcare analytics workflow on 55,500 synthetic encounters across 6 clinical conditions..."

**Screenshot:** [`healthcare-da-api-stats.png`](screenshots/healthcare-da-api-stats.png)

**Shows:**
- `total_encounters: 55500`
- 6 conditions in `clinical_conditions`: Arthritis (9308), Diabetes (9304), Hypertension (9245), Obesity (9231), Cancer (9227), Asthma (9185)

---

## 2. 11 GET Endpoints

**Bullet:** "Productized data access with a FastAPI service exposing 11 GET endpoints..."

**Screenshot:** [`healthcare-da-fastapi-docs.png`](screenshots/healthcare-da-fastapi-docs.png)

**Shows:** All 11 endpoints in Swagger UI:
1. `/` (root)
2. `/api/encounters`
3. `/api/encounters/{encounter_id}`
4. `/api/patients`
5. `/api/doctors`
6. `/api/hospitals`
7. `/api/conditions`
8. `/api/medications`
9. `/api/insurance`
10. `/api/stats`
11. `/api/search`

---

## 3. dbt Star Schema + 8 Marts + 3 Tests

**Bullet:** "Engineered a dbt star-schema warehouse with 8 core mart models plus 3 custom SQL quality checks..."

**Proof File:** [`outputs/02_dbt_proof/dbt_run_results_2026-03-11.json`](outputs/02_dbt_proof/dbt_run_results_2026-03-11.json)

**Shows:**
- `fact_patient_encounters` model: `"status": "success"`, `0.93s` execution time
- 8 mart models in `dbt-project/models/marts/core/*.sql`
- 3 test files in `dbt-project/tests/`

**Terminal proof:**
```bash
cd dbt-project && source ../.venv/bin/activate && dbt run --select fact_patient_encounters
# Result: 1 of 1 OK created sql view model dbo.fact_patient_encounters [OK in 0.93s]
```

---

## 4. Power BI Semantic Model (TMDL) + Microsoft Fabric

**Bullet:** "Delivered a code-first Power BI semantic model (TMDL/DAX) with table definitions, relationships, and reporting measures..."

**Screenshots:**
- [`healthcare-da-fabric-workspace.png`](screenshots/healthcare-da-fabric-workspace.png) - Fabric workspace with Lakehouse
- [`healthcare-da-fabric-lakehouse.png`](screenshots/healthcare-da-fabric-lakehouse.png) - Lakehouse with `healthcare_encounters` table

**Proof Files:**
- TMDL source: [`powerbi-model/model.tmdl`](powerbi-model/model.tmdl), [`powerbi-model/relationships.tmdl`](powerbi-model/relationships.tmdl)
- Fabric proof: [`outputs/03_bi_proof/fabric_lakehouse_proof_2026-03-15.md`](outputs/03_bi_proof/fabric_lakehouse_proof_2026-03-15.md)

**Shows:**
- Lakehouse `HealthcareAnalytics` created via API
- Table `healthcare_encounters` (1,000 records, Delta format)
- Service principal authentication working

---

## 5. XGBoost + MLflow (Optional)

**Bullet:** "Trained and tracked an XGBoost-based readmission workflow with MLflow metric logging..."

**Proof File:** [`outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md`](outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md)

**Shows:**
- **Accuracy:** 0.6641
- **AUC-ROC:** 0.5097
- **Dataset:** 55,500 records (44,400 train / 11,100 test)
- **Top Features:** Gender (0.1504), Blood Type (0.1421), Billing Amount (0.1345)
- MLflow tracking active

**Terminal proof:**
```bash
cd ml-pipeline/src && python3 train.py
# Result: ✅ Model training complete! ✅ Model saved to MLflow
```

---

## Quick Access

| Bullet | Screenshot | Proof File |
|--------|-----------|------------|
| 55,500 encounters + 6 conditions | `healthcare-da-api-stats.png` | `outputs/01_api_proof/api_stats_response_2026-03-11.json` |
| 11 GET endpoints | `healthcare-da-fastapi-docs.png` | `api/app/main.py` (11 route decorators) |
| dbt 8 marts + 3 tests | Terminal output | `outputs/02_dbt_proof/dbt_run_results_2026-03-11.json` |
| Power BI TMDL + Fabric | `healthcare-da-fabric-workspace.png` | `powerbi-model/*.tmdl` + `outputs/03_bi_proof/` |
| XGBoost + MLflow | Terminal output | `outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md` |

---

## Interview Talking Points

1. **Synthetic data:** Always say "synthetic" or "simulated" data explicitly.
2. **No cost savings claims:** Do not claim real hospital cost savings.
3. **AUC value:** If asked, show the MLflow run output (0.5097 AUC-ROC).
4. **Code-first:** Emphasize TMDL source control (reviewable DAX/measures in Git).
5. **CLI-able:** All Fabric operations done via API (no manual UI clicks).
