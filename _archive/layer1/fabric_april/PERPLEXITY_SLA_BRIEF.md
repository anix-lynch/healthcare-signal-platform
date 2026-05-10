# Brief for Perplexity (or any copilot) — Fabric April SLA & end goal

Paste the **block below** into Perplexity so it knows the contract, filenames, and what “done” means.

---

## COPY FROM HERE

### Project goal (why we’re doing this)

We’re building **buyer-visible proof** for Microsoft **Fabric** (Lakehouse → medallion pipeline → Warehouse SQL → Power BI Direct Lake) so a **public GitHub portfolio** and **Upwork** clients can see real Fabric UI artifacts—not only code. The repo tracks everything under **`fabric_april/`**.

**North star (from our SLA):** Ship **4** proofs in the repo: either **4 screenshots** **or** **3 screenshots + 1 pipeline JSON export** with a real pipeline body (not empty `{}`).

### Data flow (conceptual)

```
CSV on disk → Fabric Lakehouse (bronze in Files) → Data Factory pipeline (silver/gold) → Warehouse (SQL) → Power BI report (Direct Lake)
```

### Machine-checkable “done when” (strict)

All artifacts live under **`fabric_april/outputs/`**. Each **screenshot must be a real PNG (> 2 KB)**—empty placeholder files do not count.

| Phase | What “done” means |
|-------|-------------------|
| **F1 Lakehouse (bronze)** | File **`outputs/01_screenshots/lakehouse_files_explorer.png`** — Lakehouse **Explorer** showing **Files → bronze** and **Tables** (e.g. loaded table), with table preview / query success if possible. Optional text proof: **`outputs/03_proof/bronze_onelake_upload.txt`**. |
| **F2 Data Factory** | **`outputs/01_screenshots/data_factory_pipeline_run.png`** (pipeline run **Succeeded** or clear run view) **OR** **`outputs/02_exports/fabric_pipeline_definition.json`** with a **non-empty** pipeline definition (activities, not `{}`). |
| **F3 Warehouse / SQL** | **`outputs/01_screenshots/warehouse_sql_results.png`** — SQL editor or **query results grid** against the Warehouse / lakehouse SQL endpoint. |
| **F4 Power BI Direct Lake** | **`outputs/01_screenshots/powerbi_directlake_report.png`** — Power BI **report** showing it’s tied to **Direct Lake** / semantic model from this workspace. |

### Current status (update this line when sharing)

- **F1:** Done in repo (real lakehouse explorer PNG + bronze upload proof text).
- **F2:** Done — pipeline **`bronze-silver-gold`**, screenshot **`outputs/01_screenshots/data_factory_pipeline_run.png`**, narrative **`outputs/03_proof/f2_pipeline_run.txt`**.
- **F3:** Done — **`outputs/01_screenshots/warehouse_sql_results.png`**, narrative **`outputs/03_proof/f3_warehouse_sql.txt`** (HealthcareWarehouse, `SELECT TOP 100 * FROM dbo.healthcare_encounters`).
- **F4:** Done — **`outputs/01_screenshots/powerbi_directlake_report.png`**, note **`outputs/03_proof/f4_directlake_report.txt`**. **All four phases complete.**

### Workspace context (for navigation)

- Fabric workspace id (example from our links): **`577de43f-21b4-479e-99b6-ea78f32e5216`**
- Lakehouse id (example): **`28903c65-fb33-4a32-96ec-73898f26b13f`**
- Lakehouse name: **HealthcareAnalytics** (typical)

Adjust if your tenant URLs differ.

### What we need from you (Perplexity)

1. For each missing phase (**F2–F4**), give **step-by-step Fabric UI navigation** (clicks/menus) to reach a screen that matches the SLA description.
2. Say exactly **what must be visible** in the screenshot so it clearly satisfies the row above (e.g. “Succeeded” for pipeline, result grid for SQL, Direct Lake indicator for report).
3. If JSON export is easier than F2 screenshot, explain how to **export pipeline definition** from Data Factory / Fabric so we can save **`fabric_pipeline_definition.json`** with real content.

### Out of scope (don’t burn trial on this)

Eventstreams, KQL-heavy work, heavy Copilot—see strategy memo **`fabric_April20.md`** in repo parent.

## COPY TO HERE

---

Canonical sources in repo: **`fabric_april/SLA.md`**, **`fabric_april/DASHBOARD.md`**.

---

## No-Perplexity fallback: exact UI targets for F2-F4

If Perplexity is out of tokens, use this directly. The goal is not “pretty screenshot”; the goal is **unambiguous proof** that the Fabric UI artifact exists.

### F2 Data Factory pipeline proof

**Target screen:** a Fabric pipeline editor or run-results screen that clearly shows a real pipeline and a successful run.

**This repo (healthcare):** pipeline **`bronze-silver-gold`**, **HealthcareAnalytics.healthcare_encounters** → **HealthcareWarehouse.dbo.healthcare_encounters**, Full copy, run **Succeeded** — details in **`outputs/03_proof/f2_pipeline_run.txt`**. Tutorial taxi steps below are optional if you need a quick generic path.

**Fastest path based on Microsoft Learn:**

1. Open Fabric and switch into the target workspace.
2. Select **+ New item**.
3. Search for and create **Pipeline**.
4. In the new pipeline, select **Copy data assistant**.
5. Choose a source. If you only need proof fast, Microsoft’s tutorial uses **Sample data → NYC Taxi - Green**.
6. For destination, choose **Lakehouse** and connect to the target lakehouse.
7. In mapping, send output to **Tables** and give the destination table a real name.
8. Save the pipeline.
9. Select **Run**.
10. Open the **Output** tab below the canvas and click into the run details if needed.

**What must be visible in the screenshot (`data_factory_pipeline_run.png`):**

- The pipeline canvas or run page.
- At least one real activity node, not an empty canvas.
- A visible success signal such as **Succeeded** or a completed run row.
- Workspace/pipeline context somewhere on screen if possible.

**Fallback if screenshot is awkward:** export the pipeline definition and save it as `outputs/02_exports/fabric_pipeline_definition.json`. The file must contain a real pipeline body with activities, not empty `{}`. If the UI only gives you copy/download of definition text rather than a formal export button, that still counts as long as the saved file is valid JSON with activity content.

### F3 Warehouse / SQL proof

**Target screen:** Warehouse or SQL analytics endpoint with a query editor and visible results grid.

**Fastest path:**

1. Open the Fabric workspace.
2. Open the **Warehouse** item, or if you only have a Lakehouse SQL endpoint, open that SQL endpoint.
3. Start a **New SQL query** or **New visual query**.
4. Run a simple query against a real table, for example:

```sql
SELECT TOP 100 *
FROM Bronze;
```

If `Bronze` is not the actual table name, use the loaded table shown in Explorer.

**What must be visible in the screenshot (`warehouse_sql_results.png`):**

- The SQL editor or visual query editor.
- The object explorer or table context if possible.
- A populated results grid, not just the query text.
- Enough columns/rows visible that it reads as live query output.

### F4 Power BI Direct Lake proof

**Target screen:** Power BI report backed by a semantic model in **Direct Lake** mode.

**Fastest path:**

1. In the Fabric workspace, create or open a semantic model sourced from the lakehouse or warehouse.
2. Open it in Power BI report authoring.
3. Add a simple table, card, or bar chart using fields from the semantic model.
4. Make sure the model/report context shows it is connected through **Direct Lake**. This can be visible in the semantic model details, model settings, or related pane depending on the current UI.

**What must be visible in the screenshot (`powerbi_directlake_report.png`):**

- A real rendered report visual.
- The semantic model/report name.
- A visible **Direct Lake** label, storage mode indicator, or semantic model details tying the report to Direct Lake.
- Workspace context if possible.

**Important:** if the report is visible but the Direct Lake indicator is not, the screenshot is weak proof. Prefer a view that shows both the report and the model/storage-mode context, or take the screenshot from the semantic model/report area where **Direct Lake** is explicitly shown.

### Minimal capture order if trial time is tight

1. F2: get a pipeline with one copy activity and a **Succeeded** run.
2. F3: run one query and capture the results grid.
3. F4: get one report visual plus a visible **Direct Lake** indicator.

### Official docs used for this fallback

- Data Factory pipeline tutorial: <https://learn.microsoft.com/en-us/fabric/data-factory/tutorial-end-to-end-pipeline>
- Warehouse visual query editor: <https://learn.microsoft.com/en-us/fabric/data-warehouse/visual-query-editor>
- Direct Lake overview: <https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview>
