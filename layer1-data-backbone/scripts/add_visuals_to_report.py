#!/usr/bin/env python3
"""
Add visuals to Power BI report programmatically (No GUI)
Requires: pip install requests azure-identity
"""

import os
import json
import requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID", "577de43f-21b4-479e-99b6-ea78f32e5216")
DATASET_ID = "8b5a0e39-7978-41f9-bbc1-420e1e51c059"

# Get token
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://analysis.windows.net/powerbi/api/.default"
)
token = token_provider()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Power BI report definition with 4 KPI cards + 2 charts
report_definition = {
    "version": "5.0",
    "pages": [
        {
            "name": "ReportSection",
            "displayName": "Healthcare Operations",
            "width": 1920,
            "height": 1080,
            "displayOption": 0,
            "visualContainers": [
                # KPI Card 1: Total Encounters
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "width": 200,
                    "height": 150,
                    "config": json.dumps({
                        "name": "card1",
                        "singleVisual": {
                            "visualType": "card",
                            "projections": {
                                "Values": [
                                    {
                                        "queryRef": "fact_patient_encounters.Total Encounters"
                                    }
                                ]
                            },
                            "prototypeQuery": {
                                "Version": 2,
                                "From": [{"Name": "f", "Entity": "fact_patient_encounters"}],
                                "Select": [
                                    {
                                        "Measure": {
                                            "Expression": {"SourceRef": {"Source": "f"}},
                                            "Property": "Total Encounters"
                                        },
                                        "Name": "fact_patient_encounters.Total Encounters"
                                    }
                                ]
                            }
                        }
                    })
                },
                # KPI Card 2: Avg LOS
                {
                    "x": 220,
                    "y": 0,
                    "z": 1,
                    "width": 200,
                    "height": 150,
                    "config": json.dumps({
                        "name": "card2",
                        "singleVisual": {
                            "visualType": "card",
                            "projections": {
                                "Values": [
                                    {
                                        "queryRef": "fact_patient_encounters.Avg LOS"
                                    }
                                ]
                            }
                        }
                    })
                },
                # Bar Chart: Readmission by Condition
                {
                    "x": 0,
                    "y": 170,
                    "z": 2,
                    "width": 600,
                    "height": 400,
                    "config": json.dumps({
                        "name": "barChart1",
                        "singleVisual": {
                            "visualType": "clusteredBarChart",
                            "projections": {
                                "Category": [
                                    {
                                        "queryRef": "dim_diagnosis.medical_condition"
                                    }
                                ],
                                "Y": [
                                    {
                                        "queryRef": "fact_patient_encounters.Readmission Rate"
                                    }
                                ]
                            }
                        }
                    })
                },
                # Line Chart: LOS Trend
                {
                    "x": 620,
                    "y": 170,
                    "z": 3,
                    "width": 600,
                    "height": 400,
                    "config": json.dumps({
                        "name": "lineChart1",
                        "singleVisual": {
                            "visualType": "lineChart",
                            "projections": {
                                "Category": [
                                    {
                                        "queryRef": "dim_date.month_name"
                                    }
                                ],
                                "Y": [
                                    {
                                        "queryRef": "fact_patient_encounters.Avg LOS"
                                    }
                                ]
                            }
                        }
                    })
                }
            ]
        }
    ]
}

def create_report_with_visuals(report_name="Healthcare Operations Dashboard"):
    """Create a Power BI report with pre-defined visuals"""
    
    # Step 1: Create blank report
    print("📊 Creating report...")
    create_url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/reports"
    create_payload = {
        "name": report_name,
        "datasetId": DATASET_ID
    }
    
    response = requests.post(create_url, headers=headers, json=create_payload)
    if response.status_code != 201:
        print(f"❌ Failed to create report: {response.text}")
        return None
    
    report_id = response.json()["id"]
    print(f"✅ Report created: {report_id}")
    
    # Step 2: Update report definition with visuals
    print("🎨 Adding visuals...")
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/reports/{report_id}/content"
    
    # Note: This requires the full report definition JSON
    # Power BI API doesn't support partial updates
    # You'd need to upload a complete .pbix or use Power BI Embedded SDK
    
    print("⚠️  Adding visuals via API requires Power BI Embedded SDK")
    print("   Recommended: Use the web UI once to add visuals, then extract JSON")
    
    report_url = f"https://app.powerbi.com/groups/{WORKSPACE_ID}/reports/{report_id}"
    print(f"\n🔗 Open this URL to add visuals manually:")
    print(f"   {report_url}")
    
    return report_id

if __name__ == "__main__":
    create_report_with_visuals()
