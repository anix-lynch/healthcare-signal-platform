# Input Context: ML Training Snapshot

**What goes IN:** Training dataset snapshot (e.g. parquet/csv) used for the readmission model. Enables reproducible MLflow runs.

Expected filename: readmission_training_dataset_2026-03-11.parquet

How to get it:
1. Materialize the train-ready feature set from dbt outputs.
2. Export with run date in filename for traceability.

How agent uses it:
- Reproducible training and metric capture in MLflow.
