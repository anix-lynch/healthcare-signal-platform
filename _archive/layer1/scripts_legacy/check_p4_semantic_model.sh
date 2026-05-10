#!/usr/bin/env bash
# P4 check via CLI: list datasets (semantic models) in Fabric workspace via Power BI API.
# Exit 0 if workspace has at least one dataset; else 1.
# Auth: sources global.env + fabric.env; uses AZURE_CLIENT_ID/SECRET/TENANT for service-principal login if no token.

set -euo pipefail
PBI_RESOURCE="https://analysis.windows.net/powerbi/api"
GLOBAL_ENV="${HOME}/.config/secrets/global.env"
SECRETS_FILE="${HOME}/.config/secrets/fabric.env"
[[ -f "$GLOBAL_ENV" ]] && source "$GLOBAL_ENV"
[[ -f "$SECRETS_FILE" ]] && source "$SECRETS_FILE"

WORKSPACE_ID="${FABRIC_WORKSPACE_ID:-}"
[[ -z "$WORKSPACE_ID" && -f "$SECRETS_FILE" ]] && WORKSPACE_ID=$(grep -E '^export FABRIC_WORKSPACE_ID=' "$SECRETS_FILE" | head -n1 | cut -d'=' -f2- | tr -d '"' || true)

if [[ -z "$WORKSPACE_ID" ]]; then
  echo "FABRIC_WORKSPACE_ID not set (fabric.env or env)" >&2
  exit 1
fi

TOKEN=$(az account get-access-token --resource "$PBI_RESOURCE" --query accessToken -o tsv 2>/dev/null || true)
if [[ -z "$TOKEN" && -n "${AZURE_CLIENT_ID:-}" && -n "${AZURE_CLIENT_SECRET:-}" && -n "${AZURE_TENANT_ID:-}" ]]; then
  az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" -o none 2>/dev/null || true
  TOKEN=$(az account get-access-token --resource "$PBI_RESOURCE" --query accessToken -o tsv 2>/dev/null || true)
fi
if [[ -z "$TOKEN" ]]; then
  echo "No Power BI token. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID in global.env (and FABRIC_WORKSPACE_ID in fabric.env)." >&2
  exit 1
fi

RESP=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/datasets")
BODY="${RESP%$'\n'*}"
CODE="${RESP##*$'\n'}"

if [[ "$CODE" != "200" ]]; then
  echo "API returned HTTP $CODE" >&2
  echo "$BODY" | head -c 500 >&2
  exit 1
fi

COUNT=$(echo "$BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('value',[])))" 2>/dev/null || echo "0")
if [[ "${COUNT:-0}" -gt 0 ]]; then
  echo "P4 check OK: $COUNT dataset(s) in workspace $WORKSPACE_ID"
  echo "$BODY" | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\"  - {x.get('name')} ({x.get('id')})\") for x in d.get('value',[])]" 2>/dev/null || true
  exit 0
fi

echo "P4 check: no datasets in workspace (deploy semantic model or create dataset)" >&2
exit 1
