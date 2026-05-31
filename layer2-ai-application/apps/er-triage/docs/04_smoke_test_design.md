# Smoke Test Design — The Regression Gate

> **Source:** `mj/docs/autotagging_llm_as_classifier_intake_automation.md`

## The contract

```
ER3 ships when smoke test passes.
ER3 stops shipping when smoke test fails.
No exceptions.
```

## Three test layers

### Layer 1 · Golden set (must always pass)

`tests/test_smoke_esi.py` runs against `inputs/golden_esi.json`:
- 30 hand-labeled cases
- Must classify within ±1 of expected tier
- Safety-critical cases must classify ≤ 2

### Layer 2 · Safety overrides (must always pass)

`tests/test_safety_overrides.py`:
- Mock LLM giving wrong (too-high) tier on red-flag cases
- Verify Safety Agent overrides correctly
- Verify audit trail captures the override

### Layer 3 · Drift alerts (must always pass)

`tests/test_drift_alerts.py`:
- Synthetic 30% perturbation → MUST alert
- Identical embeddings → MUST NOT alert (no false positives)

## CI integration

```yaml
# .github/workflows/ci.yml (when added)

on: [push, pull_request]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: make smoke   # blocks merge if fails
      - run: make test    # full suite
```

## Why this matters

ER2 today: "I built it." (good)
ER3 with smoke tests: "I built it AND I operate it." (great — senior signal)
ER3 with smoke tests + drift alerts: "I built it AND I operate it AND I have evidence it's still working." (best — what regulated industries actually want)
