# Power BI Dashboard Automation (CLI-First Approach)

For engineers who hate GUIs and want everything scriptable.

## The Reality Check

**Power BI visual definitions are complex JSON** (500+ lines per visual). Microsoft doesn't officially support creating visuals purely via REST API — they expect you to use:
1. Power BI Desktop (GUI)
2. Power BI Embedded SDK (JavaScript/TypeScript)
3. Power BI REST API (for metadata only, not visual layout)

## What This Script Does

### `create_powerbi_dashboard.sh` (Bash)
- ✅ Creates a blank report via API
- ✅ Links it to your semantic model
- ✅ Exports screenshot (if Premium capacity)
- ❌ Cannot add visuals (API limitation)

### `add_visuals_to_report.py` (Python)
- ✅ Shows the visual definition structure
- ✅ Demonstrates how to structure the JSON
- ❌ Cannot upload visual definitions (requires Embedded SDK)

## The Hybrid Workflow (Recommended)

### Step 1: Create Report Shell (CLI)
```bash
./scripts/create_powerbi_dashboard.sh
```

This creates an empty report at:
```
https://app.powerbi.com/groups/{workspace-id}/reports/{report-id}
```

### Step 2: Add Visuals (One-Time GUI)
Open the URL from Step 1 and:
1. Click "+ Add visual"
2. Drag 4 fields to create KPI cards
3. Drag 2 charts
4. Click "Save"

**Time: 10 minutes**

### Step 3: Extract Definition (CLI)
```bash
# Download the report
az rest --method GET \
  --url "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports/${REPORT_ID}/content" \
  --resource https://analysis.windows.net/powerbi/api \
  > dashboard_definition.json
```

### Step 4: Version Control (CLI)
```bash
git add dashboard_definition.json
git commit -m "Add Power BI dashboard definition"
```

Now you have:
- ✅ Reproducible dashboard (JSON in Git)
- ✅ CLI deployment script
- ✅ Automation-ready workflow

## Future Deployments (CLI-Only)

Once you have `dashboard_definition.json`, you can deploy to new workspaces:

```bash
# Deploy to staging workspace
WORKSPACE_ID="staging-workspace-id" \
  ./scripts/deploy_dashboard_from_json.sh dashboard_definition.json

# Deploy to production workspace
WORKSPACE_ID="prod-workspace-id" \
  ./scripts/deploy_dashboard_from_json.sh dashboard_definition.json
```

## Why This Matters for Your Resume

**Before:** "I built a Power BI dashboard" (everyone says this)

**After:** "I automated Power BI dashboard deployment via REST API with version-controlled JSON definitions, enabling CI/CD for BI artifacts"

This shows:
- ✅ You understand infrastructure-as-code
- ✅ You can automate "GUI-only" tools
- ✅ You think like a platform engineer, not just an analyst

## Alternative: Power BI Embedded SDK

If you want **full CLI control** without any GUI:

```typescript
// Using @microsoft/powerbi-client
import { service, models } from 'powerbi-client';

const report = await powerbi.createReport(workspace, {
  datasetId: 'your-dataset-id',
  pages: [{
    name: 'Page1',
    visuals: [{
      type: 'card',
      x: 0, y: 0, width: 200, height: 150,
      dataRoles: [{
        name: 'Values',
        kind: models.VisualDataRoleKind.Measure
      }]
    }]
  }]
});
```

But this requires:
- Node.js/TypeScript setup
- Power BI Embedded capacity ($$)
- More complex than the hybrid approach

## Bottom Line

**For your portfolio:**
1. Use the bash script to create the report shell (shows automation)
2. Add visuals in GUI once (10 min, not worth fighting)
3. Extract JSON and commit to Git (shows version control)
4. Add deployment script (shows CI/CD thinking)

**You get 90% of the "automation cred" with 10% of the pain.**

## Run It Now

```bash
cd /Users/anixlynch/dev/00_portfolio/06devrel/orbit_karma/Powerbi/healthcare-da
./scripts/create_powerbi_dashboard.sh
```

Then open the URL it prints and spend 10 minutes dragging visuals.

**That's the pragmatic engineer approach.**
