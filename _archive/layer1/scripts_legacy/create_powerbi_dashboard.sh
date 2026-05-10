#!/usr/bin/env bash
set -euo pipefail

# Create Power BI Dashboard via CLI (No GUI)
# Requires: Azure CLI, jq, curl

WORKSPACE_ID="${FABRIC_WORKSPACE_ID:-577de43f-21b4-479e-99b6-ea78f32e5216}"
DATASET_ID="8b5a0e39-7978-41f9-bbc1-420e1e51c059"
REPORT_NAME="Healthcare Operations Dashboard"

echo "🏥 Creating Power BI dashboard via API..."

# Get Power BI API token
TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)

if [[ -z "$TOKEN" ]]; then
  echo "❌ Failed to get Power BI token. Run: az login"
  exit 1
fi

# Step 1: Create blank report
echo "📊 Creating blank report..."
REPORT_JSON=$(curl -s -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${REPORT_NAME}\",
    \"datasetId\": \"${DATASET_ID}\"
  }")

REPORT_ID=$(echo "$REPORT_JSON" | jq -r '.id')

if [[ -z "$REPORT_ID" || "$REPORT_ID" == "null" ]]; then
  echo "❌ Failed to create report"
  echo "$REPORT_JSON"
  exit 1
fi

echo "✅ Report created: $REPORT_ID"

# Step 2: Get report URL
REPORT_URL="https://app.powerbi.com/groups/${WORKSPACE_ID}/reports/${REPORT_ID}"
echo "🔗 Report URL: $REPORT_URL"

# Step 3: Export screenshot (requires Premium capacity)
echo "📸 Exporting screenshot..."
EXPORT_JSON=$(curl -s -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports/${REPORT_ID}/ExportTo" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "PNG",
    "powerBIReportConfiguration": {
      "defaultBookmark": {
        "state": "{}"
      }
    }
  }')

EXPORT_ID=$(echo "$EXPORT_JSON" | jq -r '.id')

if [[ -n "$EXPORT_ID" && "$EXPORT_ID" != "null" ]]; then
  echo "⏳ Waiting for export to complete..."
  sleep 5
  
  # Download screenshot
  curl -s -X GET \
    "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports/${REPORT_ID}/exports/${EXPORT_ID}/file" \
    -H "Authorization: Bearer $TOKEN" \
    -o "../screenshots/healthcare-dashboard-powerbi.png"
  
  echo "✅ Screenshot saved: screenshots/healthcare-dashboard-powerbi.png"
else
  echo "⚠️  Screenshot export requires Premium capacity (skipping)"
fi

echo ""
echo "✅ Dashboard created successfully!"
echo "🔗 View at: $REPORT_URL"
echo ""
echo "Next steps:"
echo "  1. Open the URL above to see your dashboard"
echo "  2. Add visuals via Power BI REST API (see scripts/add_visuals_to_report.py)"
echo "  3. Or manually add visuals in the web UI (one-time setup)"
