#!/usr/bin/env bash
set -euo pipefail

# Fabric Doctor: quick CLI diagnostics for Fabric auth/workspace/warehouse readiness

PBI_RESOURCE="https://analysis.windows.net/powerbi/api"
FABRIC_RESOURCE="https://api.fabric.microsoft.com/"
SECRETS_FILE="${HOME}/.config/secrets/fabric.env"

say() {
  printf "%s\n" "$1"
}

ok() {
  printf "[OK] %s\n" "$1"
}

warn() {
  printf "[WARN] %s\n" "$1"
}

err() {
  printf "[ERR] %s\n" "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing command: $1"
    return 1
  fi
  return 0
}

get_token() {
  local resource="$1"
  az account get-access-token --resource "$resource" --query accessToken -o tsv 2>/dev/null || true
}

load_workspace_id() {
  if [[ -n "${FABRIC_WORKSPACE_ID:-}" ]]; then
    printf "%s" "$FABRIC_WORKSPACE_ID"
    return 0
  fi

  if [[ -f "$SECRETS_FILE" ]]; then
    local id
    id=$(grep -E '^export FABRIC_WORKSPACE_ID=' "$SECRETS_FILE" | head -n1 | cut -d'=' -f2- | tr -d '"' || true)
    if [[ -n "$id" ]]; then
      printf "%s" "$id"
      return 0
    fi
  fi

  printf ""
}

main() {
  say "Fabric Doctor"
  say "-------------"

  local missing=0
  require_cmd az || missing=1
  require_cmd curl || missing=1
  require_cmd python3 || missing=1

  if [[ "$missing" -ne 0 ]]; then
    err "Install missing dependencies and rerun."
    exit 1
  fi

  if ! az account show >/dev/null 2>&1; then
    err "Azure CLI not authenticated. Run: az login"
    exit 1
  fi
  ok "Azure CLI authenticated"

  local pbi_token fabric_token
  pbi_token=$(get_token "$PBI_RESOURCE")
  fabric_token=$(get_token "$FABRIC_RESOURCE")

  if [[ -z "$pbi_token" ]]; then
    warn "Could not get Power BI token"
  else
    ok "Power BI token acquired"
  fi

  if [[ -z "$fabric_token" ]]; then
    warn "Could not get Fabric API token. Some orgs only allow Power BI scope."
  else
    ok "Fabric API token acquired"
  fi

  if [[ -z "$pbi_token" && -z "$fabric_token" ]]; then
    err "No usable Fabric/Power BI access token found"
    say "Try:"
    say "  az login"
    say "  az account show"
    say "  az account get-access-token --resource https://analysis.windows.net/powerbi/api"
    exit 1
  fi

  local workspace_id
  workspace_id=$(load_workspace_id)

  if [[ -z "$workspace_id" ]]; then
    warn "FABRIC_WORKSPACE_ID not set"
    say "Next:"
    say "  1) Create/select workspace in Fabric UI"
    say "  2) Export FABRIC_WORKSPACE_ID in $SECRETS_FILE"
    say "  3) Rerun this script"
  else
    ok "Workspace ID found: $workspace_id"
  fi

  say ""
  if [[ -n "$pbi_token" ]]; then
    say "Workspace list (Power BI API):"
    local groups_json
    groups_json=$(curl -s -H "Authorization: Bearer $pbi_token" "https://api.powerbi.com/v1.0/myorg/groups" || true)
    python3 - <<'PY' "$groups_json"
import json, sys
raw = sys.argv[1]
try:
    obj = json.loads(raw)
except Exception:
    print("[ERR] Could not parse workspace list response")
    raise SystemExit(0)
for g in obj.get("value", [])[:20]:
    name = g.get("name")
    gid = g.get("id")
    cap = g.get("isOnDedicatedCapacity")
    print(f"- {name} | {gid} | dedicated_capacity={cap}")
PY
  else
    warn "Skipping workspace list because Power BI token is unavailable"
  fi

  if [[ -n "$workspace_id" ]]; then
    if [[ -n "$pbi_token" ]]; then
      say ""
      say "Workspace capacity check:"
      local ws_json
      ws_json=$(curl -s -H "Authorization: Bearer $pbi_token" "https://api.powerbi.com/v1.0/myorg/groups/$workspace_id" || true)
      python3 - <<'PY' "$ws_json"
import json, sys
raw = sys.argv[1]
try:
    obj = json.loads(raw)
except Exception:
    print("[WARN] Could not parse workspace details")
    raise SystemExit(0)
if obj.get("id"):
    print(f"- name={obj.get('name')}")
    print(f"- id={obj.get('id')}")
    print(f"- isOnDedicatedCapacity={obj.get('isOnDedicatedCapacity')}")
else:
    print(f"[WARN] workspace detail response: {obj}")
PY
  fi

    if [[ -n "$fabric_token" ]]; then
      say ""
      say "Warehouse check (Fabric API):"
      local items_json
      items_json=$(curl -s -H "Authorization: Bearer $fabric_token" "https://api.fabric.microsoft.com/v1/workspaces/$workspace_id/items?type=Warehouse" || true)
      python3 - <<'PY' "$items_json"
import json, sys
raw = sys.argv[1]
try:
    obj = json.loads(raw)
except Exception:
    print("[WARN] Could not parse Fabric items response")
    raise SystemExit(0)
items = obj.get("value", [])
if items:
    for it in items:
      print(f"- warehouse={it.get('displayName')} | id={it.get('id')}")
else:
    print("- no warehouse found")
    print("  Next: create warehouse in workspace or via Fabric API")
PY
    fi
  fi

  say ""
  say "Recommended next commands:"
  say "  ./scripts/fabric_api_helper.sh list_workspaces"
  say "  cd dbt-project && dbt run && dbt test"
}

main "$@"
