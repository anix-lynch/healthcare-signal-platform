# Resume Claim Traceability

Map each resume bullet to code location, command, output artifact, and pass/fail.

| Claim | Code / command | Proof artifact | Status |
|-------|----------------|----------------|--------|
| 55,500 encounters, 11 endpoints | api/app/main.py, ./scripts/start_api.sh | outputs/01_api_proof/api_stats_response_2026-03-11.json | ✅ |
| dbt star schema, 8 marts, 3 checks | dbt-project/models/, tests/ | outputs/02_dbt_proof/ (run requires dbt-fabric) | ⬜ adapter |
| Power BI semantic model (TMDL) | powerbi-model/, check_p4_semantic_model.sh | outputs/03_bi_proof/semantic_model_validation_2026-03-11.md | ✅ |
| XGBoost + MLflow (optional) | ml-pipeline/src/train.py | outputs/04_ml_proof/ (requires mlflow install) | ⬜ deps |

Source: sla (locked bullets + claim-to-code map).
