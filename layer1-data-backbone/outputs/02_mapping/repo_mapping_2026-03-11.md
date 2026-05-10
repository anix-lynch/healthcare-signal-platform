# Repository Mapping Summary

Generated: 2026-03-11

## Execution Layers

1. API layer: api/
2. Warehouse layer: dbt-project/
3. Semantic layer: powerbi-model/
4. ML layer: ml-pipeline/

## Operational Scripts

- scripts/start_api.sh
- scripts/fabric_doctor.sh
- scripts/resume-proof-verification.sh
- scripts/get_fabric_info.py

## Inputs

- inputs/01_api_export
- inputs/02_fabric_profile
- inputs/03_semantic_model
- inputs/04_ml_training_snapshot

## Outputs

- outputs/01_api_proof
- outputs/02_dbt_proof
- outputs/02_schema
- outputs/02_mapping
- outputs/03_bi_proof
- outputs/04_ml_proof
- outputs/05_resume_proof

## Canonical Tracking Files

- SPEC.md (single source of truth)
- DASHBOARD.md (phase status + flow)
- README.md (entrypoint + backup note)
