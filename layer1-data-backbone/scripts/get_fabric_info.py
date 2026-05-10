import subprocess
import json
import requests
import sys

def get_token(resource):
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting token: {e.stderr}")
        return None

def get_warehouse_info(workspace_id):
    # Try Fabric API scope
    token = get_token("https://api.fabric.microsoft.com/")
    if not token:
        print("Failed to get token for Fabric API")
        return

    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type=Warehouse"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Calling {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        warehouses = data.get("value", [])
        if warehouses:
            warehouse_id = warehouses[0]["id"]
            warehouse_name = warehouses[0]["displayName"]
            print(f"\nFound warehouse: {warehouse_name} (ID: {warehouse_id})")
            
            # Get warehouse connection details
            detail_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{warehouse_id}"
            detail_response = requests.get(detail_url, headers=headers)
            
            # Also try to get SQL endpoint
            sql_endpoint_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{warehouse_id}/sqlEndpoint"
            sql_response = requests.get(sql_endpoint_url, headers=headers)
            if sql_response.status_code == 200:
                sql_data = sql_response.json()
                print("\nSQL Endpoint details:")
                print(json.dumps(sql_data, indent=2))
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print("\nWarehouse details:")
                print(json.dumps(detail_data, indent=2))
                
                # Check provisioning status
                state = detail_data.get("state", "Unknown")
                print(f"\n📊 Warehouse State: {state}")
                
                # Try to extract connection string
                if "connectionString" in detail_data:
                    print(f"\n✅ Connection String: {detail_data['connectionString']}")
                    return detail_data['connectionString']
                elif "server" in detail_data:
                    print(f"\n✅ Server: {detail_data['server']}")
                    return detail_data['server']
                elif "connectionInfo" in detail_data:
                    conn_info = detail_data['connectionInfo']
                    if isinstance(conn_info, dict) and "server" in conn_info:
                        print(f"\n✅ Server from connectionInfo: {conn_info['server']}")
                        return conn_info['server']
                else:
                    # Construct from workspace and warehouse name
                    workspace_name = "HealthcareAnalytics"
                    server = f"{workspace_name}-{warehouse_name}.datawarehouse.pbidedicated.windows.net"
                    print(f"\n⚠️  Constructed Server (may need verification): {server}")
                    print(f"   Warehouse state: {state}")
                    if state != "Active":
                        print(f"   ⚠️  Warehouse is not Active yet - wait for provisioning to complete")
                    return server
            else:
                print(f"Error getting details: {detail_response.status_code} - {detail_response.text}")
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
        # Fallback to Power BI API scope if Fabric API fails (sometimes scopes are tricky)
        print("Retrying with Power BI API scope...")
        token = get_token("https://analysis.windows.net/powerbi/api")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error with PBI scope: {response.status_code} - {response.text}")

def create_warehouse(workspace_id, name="HealthcareWarehouse"):
    token = get_token("https://api.fabric.microsoft.com/")
    if not token:
        return

    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "displayName": name,
        "type": "Warehouse"
    }
    
    print(f"Creating Warehouse '{name}'...")
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code in [201, 202]:
        data = response.json()
        print("Warehouse created successfully!")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"Error creating warehouse: {response.status_code} - {response.text}")

if __name__ == "__main__":
    workspace_id = "577de43f-21b4-479e-99b6-ea78f32e5216"
    # Get warehouse info to find connection string
    get_warehouse_info(workspace_id)
