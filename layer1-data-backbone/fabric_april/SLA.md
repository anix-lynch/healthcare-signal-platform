# SLA.md — Fabric April proof (trial window)

# "We started because: Upwork Fabric jobs all want Lakehouse + Data Factory + Power BI; our repo was code-only until we ship visible Fabric artifacts."

## THE ONE METRIC THAT MATTERS

| Metric | Now | Target |
|--------|-----|--------|
| Fabric buyer-visible proof set in repo | 4 / 4 | **4** screenshots **or** 3 screenshots + 1 pipeline JSON export |

**Done when (machine-checkable):** All files in `fabric_april/outputs/` below exist; each screenshot **> 2 KB** (not empty); `fabric_pipeline_definition.json` is valid JSON (or markdown export if JSON is blocked by tenant policy).

## Per-phase Done when

| Phase | Done when |
|-------|-----------|
| **F1 Lakehouse (bronze)** | `outputs/01_screenshots/lakehouse_files_explorer.png` exists + shows Files/Tables for bronze load |
| **F2 Data Factory pipeline** | `outputs/01_screenshots/data_factory_pipeline_run.png` exists **or** `outputs/02_exports/fabric_pipeline_definition.json` has non-empty pipeline body |
| **F3 Warehouse / SQL** | `outputs/01_screenshots/warehouse_sql_results.png` exists (query grid or SQL editor) |
| **F4 Power BI Direct Lake** | `outputs/01_screenshots/powerbi_directlake_report.png` exists (report connected Direct Lake) |

**Prerequisite:** Auth + capacity (Bchan: azure-auth / Fabric trial). No Fabric UI work until login succeeds.

---

## Out of scope (trial budget)

- Eventstreams / KQL, heavy Copilot — see `fabric_April20.md`.
