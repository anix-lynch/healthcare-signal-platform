# Healthcare Analytics Schema Summary

Generated: 2026-03-11

## Warehouse Model (dbt)

Core star-schema assets are implemented in dbt models under dbt-project/models:

- Fact table: fact_patient_encounters
- Dimensions: patient, doctor, hospital, date, condition, payer, geography, encounter type

Validation tests include assertions for:

- No negative length of stay
- Discharge timestamp after admission timestamp
- Valid readmission logic

## Semantic Model (Power BI TMDL)

Model assets are defined in powerbi-model:

- model.tmdl
- relationships.tmdl
- tables/Date.tmdl
- tables/Doctor.tmdl
- tables/Hospital.tmdl
- tables/Patient.tmdl
- tables/Patient Encounters.tmdl

Semantic layer aligns to warehouse entities for KPI reporting and readmission analysis.

## ML Feature Surface

ML training pipeline in ml-pipeline/src uses transformed healthcare data to generate readmission risk predictions and logs evidence via MLflow.
