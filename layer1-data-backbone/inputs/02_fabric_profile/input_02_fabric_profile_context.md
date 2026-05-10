# Input Context: Fabric Profile

**What goes IN:** Workspace/tenant/warehouse metadata from Fabric (JSON). Used to decide if dbt and semantic model can run.

Expected filename: fabric_workspace_connection_2026-03-11.json

How to get it:
1. Run scripts/fabric_doctor.sh.
2. Capture workspace, tenant, and warehouse status into this JSON.

How agent uses it:
- Decides whether dbt and semantic-model deployment phases can proceed.
