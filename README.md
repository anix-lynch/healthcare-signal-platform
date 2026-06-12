# healthcare-signal-platform

> **openFDA evaluated signal platform (Bullet 5) + cross-cloud portability (Bullet 6).**
> Five cheap signals (anomaly · cluster · classify · rank · retrieval) score real openFDA
> adverse-event reports and a router measures the cost–quality tradeoff of sending fewer
> reports to the LLM. The portability slice proves the same contract reconciles across
> GCP · Fabric · AWS. Run: `python3 openfda_signals/run_signals.py`.
>
> openFDA work: `openfda_signals/` (signals + proofs) · `openfda_signals/multicloud/` (3-cloud reconcile).

---

## Layout
- `openfda_signals/` — five evaluated signals + router (Bullet 5) over real openFDA FAERS
- `openfda_signals/multicloud/` — GCP/Fabric/AWS contract reconcile (Bullet 6)
- `openfda_signals/proof/` — machine-readable receipts (bullet5_scaled_proof.json etc)
- Run: `python3 openfda_signals/run_signals_scaled.py`

*Legacy synthetic patient/ESI platform removed 2026-06-11 — this repo is openFDA only.*
