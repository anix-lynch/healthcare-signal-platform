#!/usr/bin/env bash
# Fill input/output proof artifacts. Run from repo root.
# Gate: data/raw/healthcare_dataset.csv must exist. Starts API in background, captures, then stops.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DATA_CSV="${ROOT}/data/raw/healthcare_dataset.csv"
if [[ ! -f "$DATA_CSV" ]]; then
  echo "Missing $DATA_CSV — add the 55K-row dataset (see api/README). Cannot run API."
  echo "Input/output files stay empty until the pipeline runs. Each folder's *_context.md says what goes in/out."
  exit 0
fi

echo "Starting API in background..."
(cd "$ROOT/api" && python3 app/main.py) &
API_PID=$!
trap "kill $API_PID 2>/dev/null || true" EXIT

echo "Waiting for API to be ready..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s "http://127.0.0.1:8000/api/stats" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then break; fi
  sleep 2
done

echo "Capturing API stats and encounter sample..."
mkdir -p "$ROOT/outputs/01_api_proof" "$ROOT/inputs/01_api_export"
curl -s "http://127.0.0.1:8000/api/stats" | python3 -m json.tool > "$ROOT/outputs/01_api_proof/api_stats_response_latest.json"
curl -s "http://127.0.0.1:8000/api/encounters?limit=100" | python3 -m json.tool > "$ROOT/inputs/01_api_export/encounters_export_latest.json"

echo "Written outputs/01_api_proof/api_stats_response_latest.json and inputs/01_api_export/encounters_export_latest.json"
echo "For dbt proof: cd dbt-project && dbt run && cp target/run_results.json ../outputs/02_dbt_proof/dbt_run_results_latest.json"
echo "For ML proof: run ml-pipeline/src/train.py then copy MLflow summary to outputs/04_ml_proof/"