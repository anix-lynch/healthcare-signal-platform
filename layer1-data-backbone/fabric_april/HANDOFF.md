# Handoff (Cursor ↔ Perplexity / Bchan)

## Done in repo (API-authorized)

- **Auth:** SP member on workspace `HealthcareAnalytics`; tenant `cf31c468-…`; smoke tests green.
- **Bronze:** Full `data/raw/healthcare_dataset.csv` uploaded to OneLake  
  `Files/bronze/healthcare_dataset.csv` on Lakehouse `28903c65-fb33-4a32-96ec-73898f26b13f`.  
  Run: `source ~/.config/secrets/global.env && az login --service-principal … --allow-no-subscriptions && python3 scripts/upload_bronze_to_onelake.py`  
  Requires: `certifi` (for SSL on some Mac Python builds).
- **Existing:** Managed table `healthcare_encounters` still in Lakehouse; Warehouse `HealthcareWarehouse`; semantic model **Healthcare Semantic Model**.

## Still open (not automated here)

1. **Data Factory pipeline** — bronze → silver → gold (Fabric UI or Items API + pipeline definition). Export JSON to `fabric_april/outputs/02_exports/fabric_pipeline_definition.json` when ready.
2. **Direct Lake** — bind **Healthcare Semantic Model** to Lakehouse tables / SQL endpoint in **Direct Lake** mode (Power BI / Fabric modeling tools; not a single REST one-liner in all tenants).

## Paste to Perplexity (short)

> Bronze CSV is uploaded to OneLake under `Files/bronze/healthcare_dataset.csv`. Need step-by-step for (1) minimal medallion pipeline in Fabric Data Factory for this workspace, and (2) switching the existing **Healthcare Semantic Model** to **Direct Lake** against the Lakehouse. Lakehouse id `28903c65-fb33-4a32-96ec-73898f26b13f`, workspace `577de43f-21b4-479e-99b6-ea78f32e5216`.
