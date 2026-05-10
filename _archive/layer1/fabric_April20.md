# Fabric strategy memo — April 2026 (trial ~25 days / ~Apr 20)

Source: Upwork job pattern analysis + [healthcare-da](https://github.com/anix-lynch/healthcare-da) gap check.

---

## Real Upwork jobs (2026 — active URLs)

| Theme | Link |
|--------|------|
| Medallion + API integration | [Microsoft Fabric Data Engineer — Medallion + API](https://www.upwork.com/freelance-jobs/apply/Microsoft-Fabric-Data-Engineer-700-Certified-Medallion-Architecture-API-Integration_~022036514245230263141/) |
| Customer Data Platform (3-month) | [Senior DS/DE — CDP + Microsoft Fabric](https://www.upwork.com/freelance-jobs/apply/Senior-Data-Scientist-Data-Engineer-Customer-Data-Platform-Microsoft-Fabric_~022035969382702932146/) |
| Fabric + Power BI warehouse Phase 2 | [Fabric/Power BI — enhance DW + reporting](https://www.upwork.com/freelance-jobs/apply/Microsoft-Fabric-Power-Specialist-Enhance-Existing-Data-Warehouse-Reporting-Environment_~022032705957843710940/) |
| ADF + Synapse + Fabric pipelines | [Data Engineer — pipeline development](https://www.upwork.com/freelance-jobs/apply/Experienced-Data-Engineer-Needed-for-Data-Pipeline-Development_~022020854224707639401/) |
| Fabric config (Data Factory + Warehouse) | [Assistance — Data Factory, Warehouse, Power BI](https://www.upwork.com/freelance-jobs/apply/Assistance-with-Fabric-config-with-data-factory-data-warehouse-Power_~022034697760628397770/) |
| Fabric SME — enterprise | [Microsoft Fabric SME](https://www.upwork.com/freelance-jobs/apply/Microsoft-Fabric-SME_~022031067965128014646/) |

**Pattern:** All six want **Lakehouse + Data Factory + Power BI** as the baseline.

---

## Repo snapshot — [github.com/anix-lynch/healthcare-da](https://github.com/anix-lynch/healthcare-da)

**Already in repo:**

- `api/` — FastAPI  
- `dbt-project/` — transformation logic  
- `ml-pipeline/` — MLflow  
- `powerbi-model/` — semantic model (TMDL)  
- `data/raw/` — healthcare CSVs  

**Gap:** Fabric is not wired end-to-end in the product yet — mostly local/code. Buyers want **visible Fabric artifacts** (screenshots: Lakehouse, pipelines, reports).

---

## FREE features to enable (zero extra cost — trial window)

### Priority 1 — do these first

1. **Lakehouse** — load raw CSVs (bronze); every job asks for this.  
2. **Data Factory pipeline** — bronze → silver → gold medallion flow.  
3. **Warehouse / SQL endpoint** — T-SQL for reporting (pairs with Lakehouse).  
4. **Power BI Direct Lake** — semantic model → Lakehouse in Direct Lake mode (strong differentiator).

### Priority 2 — medium

- **Notebooks (PySpark)** — bring MLflow story into Fabric where relevant.  
- **Dataflows Gen2** — simpler ETL alternative to ADF for some demos.

### Skip for now

- Eventstreams / KQL (real-time — burns trial capacity).  
- Fabric Copilot at scale (needs higher SKU — not the focus on free trial).

---

## Next steps (execution order)

Workspace: **HealthcareAnalytics** (or current Fabric workspace).

1. Create **Lakehouse** in the workspace.  
2. Load **healthcare raw** data (bronze).  
3. Build **pipeline** (medallion path).  
4. Connect **Power BI** — **Direct Lake** to semantic model / Lakehouse.  

**Billing note:** Trial window was ~25 days from late Mar 2026; align with [portal.office.com/account](https://portal.office.com/account) + Fabric profile countdown. Org tenant **Microsoft Fabric (Free)** — no PAYG Azure sub on `alynch@gozeroshot.dev` per CLI check; still cancel trial if you want capacity gone early.

---

## Verification links (agents / human)

- M365 licenses: [portal.office.com/account](https://portal.office.com/account)  
- Fabric home + trial / Cancel trials: [app.fabric.microsoft.com](https://app.fabric.microsoft.com/)  

See `AGENTS.md` for short context.

---

## Execution scaffold (repo)

Internal track folder: **`fabric_april/`** — `SLA.md`, `DASHBOARD.md`, `inputs/*`, `outputs/*` (screenshot + pipeline export placeholders). Start there after auth.
