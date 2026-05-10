# DASHBOARD — Fabric April track

**👈 we are here:** **Fabric April SLA complete** — F1–F4 ✅ (see `outputs/01_screenshots/` + `outputs/03_proof/`).

## Phase summary

| Phase | Status | Who |
|-------|--------|-----|
| F0 Auth + capacity | ⬜ | b-turn → AI |
| F1 Lakehouse + bronze CSV | ✅ | AI | 
| F2 Data Factory pipeline (medallion) | ✅ | AI |
| F3 Warehouse / SQL proof | ✅ | AI |
| F4 Power BI Direct Lake + report | ✅ | AI |

## Flow

```
[data/raw CSV] → Fabric Lakehouse (bronze) → Pipeline (silver/gold) → Warehouse SQL → Power BI Direct Lake → screenshots + export
```

## SLA STATUS

| Phase | Done when (see SLA.md) | Met |
|-------|-------------------------|-----|
| F1 | `outputs/01_screenshots/lakehouse_files_explorer.png` + `outputs/03_proof/bronze_onelake_upload.txt` | ✅ |
| F2 | `outputs/01_screenshots/data_factory_pipeline_run.png` **or** `outputs/02_exports/fabric_pipeline_definition.json` | ✅ |
| F3 | `outputs/01_screenshots/warehouse_sql_results.png` | ✅ |
| F4 | `outputs/01_screenshots/powerbi_directlake_report.png` | ✅ |

**SHIPPED:** true
