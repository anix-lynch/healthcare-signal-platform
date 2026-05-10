# Input Context: API Export

**What goes IN:** Snapshot of encounter data from the API (JSON). Used to prove API shape and demo continuity.  
If file is empty: add data/raw/healthcare_dataset.csv then run scripts/populate_proof_artifacts.sh.

Expected filename: encounters_export_2026-03-11.json

How to get it:
1. Start API via scripts/start_api.sh.
2. Pull encounter payload from /api/encounters and save as JSON snapshot.

How agent uses it:
- Validates endpoint shape and sample data continuity for demo proofs.
