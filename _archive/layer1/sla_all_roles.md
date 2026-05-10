# Resume SLA - Healthcare Analytics (All 4 Roles)

Owner: Anix Lynch  
Date created: 2026-03-17  
Rule: Every number must be explainable from code/docs in this repo.

**One repo. Four resumes. Same proof artifacts, different framing.**

---

## Role 1: Data Analyst

**Headline:** Healthcare analytics specialist | Power BI | KPIs | Business insights

**4 Bullets:**

1. Built an end-to-end healthcare analytics workflow on 55,500 synthetic encounters across 6 clinical conditions, turning raw clinical events into KPI-ready datasets for readmission, length-of-stay, and utilization reporting.

2. Designed and delivered Power BI dashboards with 4 executive KPIs (Total Encounters, Avg LOS, Readmission Rate, Avg Billing) and 3 drill-down visuals (readmission by condition, LOS trend, top hospitals), enabling administrators to identify a 22% diabetes readmission rate and prioritize care pathway improvements.

3. Productized data access with a FastAPI service exposing 11 GET endpoints (root, encounters, lookup dimensions, stats, and search) and dataset-level pagination/filtering for analyst and dashboard workflows.

4. Translated business questions into SQL queries against a star-schema warehouse (1 fact, 7 dimensions), producing ad-hoc reports on provider performance, medication effectiveness, and revenue by insurance payer.

**Proof:**
- Bullet 1: `api/app/main.py`, `outputs/01_api_proof/`
- Bullet 2: Power BI dashboard screenshots (TODO: `screenshots/powerbi_dashboard.png`)
- Bullet 3: `api/app/main.py` (11 route decorators)
- Bullet 4: `dbt-project/models/marts/core/` (star schema)

---

## Role 2: Analytics Engineer

**Headline:** dbt & data modeling expert | Star schema | SQL | Data quality

**4 Bullets:**

1. Engineered a dbt star-schema warehouse with 8 core mart models (1 fact, 7 dimensions) plus 3 custom SQL quality checks (negative LOS, discharge ordering, readmission-window validity), producing reproducible and auditable reporting outputs for 55,500 patient encounters.

2. Implemented multi-stage dbt transformations (staging → intermediate → marts) to calculate clinical KPIs including length-of-stay, 30-day readmission rates, and risk stratification, translating business requirements into reusable SQL models.

3. Designed dimensional models optimized for BI consumption, enabling analysts to query complex healthcare data with simple joins (e.g., readmission rate by condition, LOS by hospital) instead of writing complex aggregation logic.

4. Automated data quality validation with dbt tests (unique, not_null, custom SQL assertions), ensuring data integrity before downstream consumption by Power BI dashboards and ML models.

**Proof:**
- Bullet 1: `dbt-project/models/marts/core/` (8 models), `dbt-project/tests/` (3 tests), `outputs/02_dbt_proof/`
- Bullet 2: `dbt-project/models/intermediate/` (int_encounters_enriched.sql, int_readmissions.sql)
- Bullet 3: `dbt-project/models/marts/core/` (star schema design)
- Bullet 4: `dbt-project/tests/`, `outputs/02_dbt_proof/dbt_run_results_2026-03-11.json`

---

## Role 3: Data Engineer

**Headline:** Data infrastructure builder | FastAPI | ETL | Cloud (Azure/Fabric)

**4 Bullets:**

1. Built a FastAPI service with 11 REST endpoints exposing 55,500 patient encounters, implementing pagination, filtering (by condition, age, admission type), and pre-computed aggregations to support dashboard and ML workflows.

2. Engineered a multi-stage ETL pipeline transforming raw healthcare data (CSV) into a star-schema warehouse (8 marts) with automated quality checks, deployed to Microsoft Fabric using Azure service principal authentication.

3. Designed and deployed cloud infrastructure on Microsoft Fabric (Lakehouse + SQL endpoint) with OneLake API integration, automating data uploads and warehouse provisioning for scalable analytics workloads.

4. Implemented data access patterns (pagination, filtering, caching strategy) to optimize API performance for concurrent analyst and ML engineer usage, with OpenAPI documentation for self-service consumption.

**Proof:**
- Bullet 1: `api/app/main.py` (11 endpoints), `outputs/01_api_proof/`
- Bullet 2: `dbt-project/models/` (ETL pipeline), `scripts/check_p4_semantic_model.sh` (Azure auth)
- Bullet 3: `scripts/check_p4_semantic_model.sh`, Azure Fabric workspace screenshots
- Bullet 4: `api/app/main.py` (pagination, filtering), `api/README.md` (OpenAPI docs)

---

## Role 4: Applied ML Engineer

**Headline:** ML deployment & feature stores | XGBoost | MLflow | Feast

**4 Bullets:**

1. Trained and tracked an XGBoost readmission risk classifier on 55,500 patient encounters using MLflow experiment tracking, achieving 66% accuracy with interpretable feature importance (Gender 15%, Blood Type 14%, Billing Amount 13%) for clinical decision support.

2. Engineered clinical features for healthcare ML (Age, Gender, Medical Condition, Medication interactions) with domain-aware transformations (readmission target from test results, LOS calculation, emergency admission flags), preventing data leakage by dropping future information and PII.

3. Architected a Feast feature store with DynamoDB online storage, 3 feature views, and offline/online parity tests to ensure training-serving consistency and point-in-time correctness for production ML model deployment.

4. Designed ML pipeline architecture (training: XGBoost + MLflow; serving: Feast + FastAPI) to enable real-time readmission risk scoring at patient discharge, with model versioning and lineage tracking for reproducibility.

**Proof:**
- Bullet 1: `ml-pipeline/src/train.py`, `outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md`
- Bullet 2: `ml-pipeline/src/train.py` (lines 41-65: feature engineering)
- Bullet 3: `anix-lynch/feast` repo (separate project)
- Bullet 4: `ml-pipeline/src/train.py`, `docs/ML_CONTEXT.md` (serving architecture)

---

## Claim-to-Code Traceability (Shared Across All Roles)

| Claim | Code Location | Proof Artifact | Status |
|-------|---------------|----------------|--------|
| 55,500 encounters, 6 conditions | api/app/main.py, data/raw/healthcare_dataset.csv | outputs/01_api_proof/api_stats_response_2026-03-11.json | ✅ |
| 11 GET endpoints | api/app/main.py (11 route decorators) | outputs/01_api_proof/ | ✅ |
| dbt star schema, 8 marts, 3 tests | dbt-project/models/marts/core/*.sql (8 files), tests/*.sql (3 files) | outputs/02_dbt_proof/dbt_run_results_2026-03-11.json | ✅ |
| Power BI semantic model (TMDL) | powerbi-model/*.tmdl | outputs/03_bi_proof/semantic_model_validation_2026-03-11.md | ✅ |
| Power BI dashboard (4 KPIs, 3 visuals) | Power BI workspace | screenshots/powerbi_dashboard.png | ⬜ TODO |
| XGBoost + MLflow (accuracy 0.66, AUC 0.51) | ml-pipeline/src/train.py | outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md | ✅ |
| Feature importance (top 8 features) | ml-pipeline/src/train.py | outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md | ✅ |
| Feast feature store (DynamoDB, 3 views, parity tests) | anix-lynch/feast repo | feast repo README + tests/ | ⬜ External |

---

## Missing Proof Artifacts (TODO)

### 1. Power BI Dashboard Screenshot (High Priority)

**What:** Screenshot of Power BI dashboard with 4 KPI cards + 3 visuals

**Why:** Data Analyst bullet 2 needs visual proof

**How:**
1. Open Power BI workspace: `https://app.powerbi.com/groups/577de43f-21b4-479e-99b6-ea78f32e5216`
2. Create report with visuals (or use existing)
3. Export → PNG
4. Save to: `screenshots/powerbi_dashboard.png`

**Blockers:** Need to build visuals in Power BI (manual UI work)

**Alternative:** Use Power BI CLI to create report shell, then add visuals manually

---

### 2. MLflow UI Screenshot (Optional, Low Priority)

**What:** Screenshot of MLflow experiment tracking UI showing runs, metrics, feature importance

**Why:** Applied ML Engineer bullet 1 could use visual proof (but markdown summary is sufficient)

**How:**
1. Run `mlflow ui` in `ml-pipeline/` folder
2. Open `http://localhost:5000`
3. Screenshot experiment page
4. Save to: `screenshots/mlflow_experiment_tracking.png`

**Blockers:** None (can run locally)

---

### 3. Feast Feature Store Proof (External Repo)

**What:** README + parity tests from `anix-lynch/feast` repo

**Why:** Applied ML Engineer bullet 3 needs proof

**How:**
1. Clone `anix-lynch/feast` repo
2. Read README (DynamoDB setup, 3 feature views)
3. Read `tests/` (offline/online parity tests)
4. Reference in resume as separate project

**Blockers:** Need to locate/verify feast repo exists

---

## Interview Safety Notes (All Roles)

- **Synthetic data:** Always say "synthetic" or "simulated" data explicitly
- **No real savings claims:** Do not claim "$2.25M saved" — say "could save" or "estimated impact"
- **Metrics transparency:** If asked for AUC value, show the run output (0.51 AUC for this model)
- **Scope clarity:** This is a portfolio project, not production deployment
- **Team size:** Solo project (all roles = you), but frame as "I built" not "we built"

---

## Resume File Naming Convention

```
/Users/anixlynch/dev/claude_resume/_archive/
├── v18_data_analyst/
│   └── _claude_edited.md (uses bullets from Role 1)
├── v19_analytics_engineer/
│   └── _claude_edited.md (uses bullets from Role 2)
├── v20_data_engineer/
│   └── _claude_edited.md (uses bullets from Role 3)
└── v21_applied_ml_engineer/
    └── _claude_edited.md (uses bullets from Role 4)
```

Each resume points to the same repo: `anix-lynch/healthcare-analytics`

---

## Next Steps (Priority Order)

1. ✅ **Create context docs** (BUSINESS_CONTEXT, ANALYTICS_ENGINEER_CONTEXT, DATA_ENGINEER_CONTEXT, ML_CONTEXT)
2. ⬜ **Build Power BI dashboard** → Export screenshot → Update Data Analyst bullet 2 proof
3. ⬜ **Verify Feast repo** → Link in Applied ML Engineer bullet 3
4. ⬜ **Draft 4 resumes** → One per role, using bullets from this SLA
5. ⬜ **Update SPEC.md** → Add P7 (Power BI dashboard), P8 (Resume drafts)
6. ⬜ **Final review** → Human approves all 4 resumes

---

**Key Insight:** Same repo, same proof artifacts, but each resume tells a different story. Data Analyst focuses on business impact. Analytics Engineer focuses on data modeling. Data Engineer focuses on infrastructure. Applied ML Engineer focuses on ML deployment.
