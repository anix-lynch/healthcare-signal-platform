# SPEC: Healthcare Analytics Progress Tracker

**👤 5% you · 🤖 95% agent** — Human: P9 final approval (P7/P8 optional polish). Agent runs terminal with keys from local secure env.

Last updated: 2026-04-19 (P9 interview lock + showroom closeout)

## Goal

Ship an interview-ready, evidence-backed healthcare analytics stack (API → dbt → semantic model → ML) with **4 resume variants** (Data Analyst, Analytics Engineer, Data Engineer, Applied ML Engineer); every claim traceable to code per **sla_all_roles.md** (locked bullets + claim-to-code map).

**One repo, four resumes.** Same proof artifacts, different framing.

**Workflow order:** Raw data in place (55K rows) → run populate script → API/semantic proof captured → optionally install deps for dbt/ML → then all proof outputs filled. Power BI dashboard (manual UI) = optional polish for Data Analyst variant.

## Where we are · Next step

| Step | Done | Next |
| ---- | ---- | ---- |
| P0 Context + keys | ✅ | |
| P1 Scaffold repair | ✅ | |
| P1.5 Raw data loaded | ✅ | |
| P2 API proof | ✅ | |
| P3 dbt proof | ✅ | |
| P4 Semantic model proof | ✅ | |
| P5 ML proof | ✅ | |
| P6 Context docs (4 roles) | ✅ | |
| P7 Power BI dashboard | ⬜ | Optional: build visuals → screenshot (Data Analyst proof) |
| P8 Resume drafts (4 roles) | ⬜ | Optional: draft 4 resumes using sla_all_roles.md |
| P9 Final interview lock | ✅ | APPROVED 2026-04-19 — core proofs interview-ready; showroom push allowed |

## Inputs

| Input | Where it lives | Status | Who | Notes |
|-------|----------------|--------|-----|-------|
| **Raw dataset** | data/raw/healthcare_dataset.csv | ✅ | AI | Verified: 55,501 rows. Unlocks: populate script → proof outputs. |
| API export snapshot | inputs/01_api_export/encounters_export_2026-03-11.json | ✅ | AI | Captured (100 encounters sample). |
| Semantic model source | inputs/03_semantic_model/healthcare_semantic_model_v1.tmdl | ✅ | AI | TMDL source in repo. |
| Azure/Fabric auth vars | local secure env (not in repo) | ✅ | AI | Verified. Unlocks: Fabric/Power BI auth for P4 checks. |
| dbt-fabric adapter | .venv with dbt-core + dbt-fabric | ✅ | AI | Created venv; dbt run successful. Unlocks: P3 (dbt run). |
| mlflow + xgboost | pip install mlflow xgboost scikit-learn | ✅ | AI | Verified. Unlocks: P5 (ML training proof). |

## Outputs

| Output | Where it lives | Status | Who | Notes |
|--------|----------------|--------|-----|-------|
| API proof stats | outputs/01_api_proof/api_stats_response_2026-03-11.json | ✅ | AI | Captured (stats JSON: 55K encounters, demographics, financial, operational). |
| API export sample | inputs/01_api_export/encounters_export_2026-03-11.json | ✅ | AI | Captured (100 encounters). |
| dbt run proof | outputs/02_dbt_proof/dbt_run_results_2026-03-11.json | ✅ | AI | Captured (fact_patient_encounters: success, 0.93s). |
| Semantic model validation | outputs/03_bi_proof/semantic_model_validation_2026-03-11.md | ✅ | AI | P4 script passed: 1 dataset in Fabric workspace. |
| MLflow run summary | outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md | ✅ | AI | Captured (accuracy: 0.6641, AUC: 0.5097, feature importance). |
| Context docs (4 roles) | healthcare-da-public/docs/ (BUSINESS_CONTEXT, ANALYTICS_ENGINEER_CONTEXT, DATA_ENGINEER_CONTEXT, ML_CONTEXT) | ✅ | AI | P6: 4 perspective docs created. |
| Power BI dashboard screenshot | screenshots/powerbi_dashboard.png | ⬜ | Human | P7: Manual UI work (4 KPIs + 3 visuals). Unlocks: Data Analyst bullet 2 proof. |
| Resume SLA (4 roles) | sla_all_roles.md | ✅ | AI | 4 bullets per role, shared proof artifacts. |
| Resume drafts (4 roles) | claude_resume/_archive/v18-v21/ | ⬜ | AI | P8: Draft 4 resumes using sla_all_roles.md bullets. |
| Warehouse/BI schema summary | outputs/02_schema/healthcare_analytics_schema_2026-03-11.md | ✅ | AI | Scaffold doc (35 lines). |
| Repository mapping summary | outputs/02_mapping/repo_mapping_2026-03-11.md | ✅ | AI | Scaffold doc. |

## Phase Gates

| Phase | Gate | Status | Who |
|-------|------|--------|-----|
| P0 Context + keys | Read AGENT.md, TOOL_STACK_AUDIT; verify local secure env for Azure/Fabric auth | ✅ | AI |
| P1 Scaffold repair | Backup legacy scaffold; create canonical SPEC.md | ✅ | AI |
| P1.5 Raw data loaded | data/raw/healthcare_dataset.csv present (55,501 rows); run populate_proof_artifacts.sh | ✅ | AI |
| P2 API proof | Verify API stats endpoint evidence (outputs/01_api_proof/ has content) | ✅ | AI |
| P3 dbt proof | Created .venv with dbt-core + dbt-fabric; run dbt run; capture run_results.json | ✅ | AI |
| P4 Semantic model proof | Run check_p4_semantic_model.sh (auth from local service principal) | ✅ | AI |
| P5 ML proof | Install mlflow; run train.py; capture run summary | ✅ | AI |
| P6 Context docs (4 roles) | Create BUSINESS_CONTEXT, ANALYTICS_ENGINEER_CONTEXT, DATA_ENGINEER_CONTEXT, ML_CONTEXT | ✅ | AI |
| P7 Power BI dashboard | Build dashboard in Power BI UI (4 KPIs + 3 visuals) → export screenshot | ⬜ | Human |
| P8 Resume drafts (4 roles) | Draft 4 resumes (v18-v21) using sla_all_roles.md bullets | ⬜ | AI |
| P9 Final interview lock | Approve end-to-end go/no-go for all 4 resume variants | ✅ | Human |

## B-turns Pending

**P7 (Power BI dashboard) — optional human work**

Build dashboard in Power BI UI (manual work):

1. Open the Power BI workspace in the same Fabric tenant used for P4 semantic validation.
2. Create report with 4 KPI cards (Total Encounters, Avg LOS, Readmission Rate, Avg Billing).
3. Add 3 visuals (readmission by condition bar chart, LOS trend line chart, top hospitals table).
4. Export → PNG → save to `screenshots/powerbi_dashboard.png`.

**P9 (final lock):** ✅ Approved 2026-04-19 — API, dbt, semantic model, and ML proof artifacts are interview-ready; GitHub showroom push cleared. P7/P8 remain optional. Fabric/API route PNGs under `screenshots/` can be regenerated with `python3 scripts/render_proof_screenshots.py`; replace with browser captures when convenient.

## File Map

```
healthcare-da/
├── sla                          ← Original Data Analyst bullets (legacy)
├── sla_all_roles.md             ← 4 resume variants (Data Analyst, Analytics Engineer, Data Engineer, Applied ML) ← NEW
├── SPEC.md                      ← Single source of truth for progress
├── DASHBOARD.md                 ← Phase summary + flow
├── data/raw/                    ← 55,501 patient records (healthcare_dataset.csv)
├── api/                         ← FastAPI (11 endpoints)
├── dbt-project/                 ← Star schema (8 marts, 3 tests)
├── powerbi-model/               ← TMDL semantic model
├── ml-pipeline/                 ← XGBoost + MLflow
├── scripts/                     ← start_api.sh, populate_proof_artifacts.sh, check_p4_semantic_model.sh, fabric_doctor.sh, render_proof_screenshots.py
├── inputs/                      ← 01_api_export, 02_fabric_profile, 03_semantic_model, 04_ml_training_snapshot
├── outputs/                     ← 01_api_proof, 02_dbt_proof, 03_bi_proof, 04_ml_proof, 05_resume_proof, 02_schema, 02_mapping
└── screenshots/                 ← proof PNGs (see SCREENSHOTS.md); powerbi_dashboard.png (P7 optional)
```

## Proof Artifacts Status (All 4 Roles)

| Claim (from sla_all_roles.md) | Code location | Proof artifact | Status |
|-------------------------------|---------------|----------------|--------|
| 55,500 encounters, 6 conditions | api/app/main.py | outputs/01_api_proof/api_stats_response_2026-03-11.json | ✅ |
| 11 GET endpoints | api/app/main.py (11 route decorators) | outputs/01_api_proof/api_stats_response_2026-03-11.json | ✅ |
| dbt star schema, 8 marts, 3 tests | dbt-project/models/marts/core/*.sql (8 files), tests/*.sql (3 files) | outputs/02_dbt_proof/dbt_run_results_2026-03-11.json | ✅ |
| Power BI semantic model (TMDL) | powerbi-model/*.tmdl | outputs/03_bi_proof/semantic_model_validation_2026-03-11.md | ✅ |
| Power BI dashboard (4 KPIs + 3 visuals) | Power BI workspace | screenshots/powerbi_dashboard.png | ⬜ P7 |
| XGBoost + MLflow (accuracy 0.66, AUC 0.51) | ml-pipeline/src/train.py | outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md | ✅ |
| Feature importance (top 8 features) | ml-pipeline/src/train.py | outputs/04_ml_proof/mlflow_run_summary_2026-03-11.md | ✅ |
| Feast feature store (DynamoDB, 3 views) | anix-lynch/feast repo | feast repo README + tests/ | ⬜ External |
| Context docs (4 roles) | healthcare-da-public/docs/ | BUSINESS_CONTEXT, ANALYTICS_ENGINEER_CONTEXT, DATA_ENGINEER_CONTEXT, ML_CONTEXT | ✅ |

## Session Start (Agents)

1. Read local AGENT context (nudge rule + SPEC.md = only entry point).
2. Read local TOOL_STACK_AUDIT context (only suggest from approved stack).
3. Use SPEC.md as single source of truth. Never a single read/done row; break docs into actionable items.
4. Before any proof step: confirm prerequisite (raw data, keys, deps). If missing, set Status=⬜ and add to B-turns with exact command.
5. No stub .md files in outputs/. Blockers go in SPEC.md B-turns only.
