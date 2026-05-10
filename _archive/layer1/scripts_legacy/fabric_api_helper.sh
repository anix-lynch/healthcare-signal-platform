#!/bin/bash
# Fabric API Helper - Use with Azure CLI authentication
# This allows Kilo to interact with Fabric via REST API

# Get Azure CLI token for Power BI API
TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "Error: Could not get Azure CLI token. Run: az login"
    exit 1
fi

# Function to list workspaces
list_workspaces() {
    curl -s -H "Authorization: Bearer $TOKEN" \
        "https://api.powerbi.com/v1.0/myorg/groups" | python3 -m json.tool
}

# Main command router
case "$1" in
    list_workspaces)
        list_workspaces
        ;;
    *)
        echo "Fabric API Helper"
        echo "Usage: $0 list_workspaces"
        exit 1
        ;;
esac
