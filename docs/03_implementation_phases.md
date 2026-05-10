# 03 — Implementation Phases

> **What's actually shipped vs designed-but-queued.** Honest accounting per phase. When an interviewer asks *"is this in production?"* the answer points at one row of this table, not vibes.

---

## The 5-phase roadmap

```
PHASE 1 — MVP                        STATUS: ✅ shipped
PHASE 2 — INTAKE AUTOMATION          STATUS: ✅ shipped (in apps/er-triage)
PHASE 3 — PRODUCTION SAFETY          STATUS: ✅ shipped (in apps/er-triage + layer3)
PHASE 4 — MULTI-CLOUD                STATUS: ⚠️ scaffold (CloudProvider adapter + 3 stub providers)
PHASE 5 — INTEGRATION                STATUS: ⌛ queued (services/* implementation, ops + exec apps)
```

---

## Phase 1 — MVP (✅ shipped, lives in ER2 sister repo)

**What:** Rachel (retrieval) + Mad Lib (generation) + guardrails on Cloud Run with a live URL.

**Owner:** GenAI Eng / FDE.

**Evidence:**
- Live URL on Cloud Run (separate ER2 repo — production deployment)
- This repo's `layer2-ai-application/shared/retrieval` + `shared/generate` are the framework versions of those modules

**Why it shipped first:** the smallest deployable artifact that proved end-to-end (data → AI → user). Everything else builds on it.

---

## Phase 2 — Intake Automation (✅ shipped)

**What:** Auto-tag ESI tier 1-5 at intake using LLM-as-classifier. Safety Agent enforces clinical hard-rules.

**Owner:** GenAI Eng / Clinical FDE.

**Lives in:**
```
layer2-ai-application/apps/er-triage/classify/esi_classifier.py     LLM classifier
layer2-ai-application/apps/er-triage/classify/prompts.py            clinical rubric
layer2-ai-application/apps/er-triage/safety/safety_agent.py         hard-rule layer
layer2-ai-application/apps/er-triage/inputs/golden_esi.json         30-case smoke set
layer2-ai-application/apps/er-triage/tests/test_smoke_esi.py        regression gate
layer2-ai-application/apps/er-triage/tests/test_safety_overrides.py rule enforcement
```

**Evidence:** smoke tests pass on golden_esi.json. Safety overrides enforced (never down-triage red flags).

**Why this Phase mattered:** turned ER2's open-ended chat into a structured-decision system. "NOW / SOON / WAIT" is an output a charge nurse can act on; freeform LLM text is not.

---

## Phase 3 — Production Safety (✅ shipped)

**What:** Drift monitoring + per-case anomaly flagging + adversarial test suite.

**Owner:** AI Safety Eng / AI Platform Eng.

**Lives in:**
```
layer2-ai-application/shared/anomaly/drift.py                       centroid-shift drift
layer2-ai-application/shared/anomaly/anomaly_flagger.py             per-case outlier
layer2-ai-application/apps/er-triage/tests/test_drift_alerts.py     drift gate
layer3-governance/scripts/06_redteam_suite.py                        50-prompt adversarial
layer3-governance/data/redteam_block_rate.json                       100% baseline
layer2-ai-application/shared/guardrails/input_guardrails.py         spaCy + regex PII (real impl)
layer2-ai-application/shared/guardrails/output_guardrails.py        hallucination + citation
layer2-ai-application/shared/guardrails/llama_guard.py              secondary safety classifier
```

**Evidence:**
- Ragas faithfulness 0.958 / relevancy 0.856 (50-Q&A baseline)
- Red-team 100% block rate across 5 attack categories (50 prompts)
- 1,753 PII tokens redacted (spaCy + regex, verified)
- All in `layer3-governance/data/` and `apps/er-triage/outputs/baseline/`

**Why this Phase mattered:** *Drift monitoring is the regulator's favorite metric.* Every health-system AI procurement RFP asks about it. Without Phase 3, you can demo but can't sell.

---

## Phase 4 — Multi-Cloud (⚠️ scaffold)

**What:** Same code runs on Vertex / Azure / AWS via `CloudProvider` adapter. Customer picks cloud via env var.

**Owner:** AI Platform Architect.

**Lives in:**
```
layer2-ai-application/shared/cloud/adapter.py                CloudProvider Protocol
layer2-ai-application/shared/cloud/factory.py                env-driven selection
layer2-ai-application/shared/cloud/vertex_provider.py        default (uses GCP credit)
layer2-ai-application/shared/cloud/azure_provider.py         Microsoft-shop deployments
layer2-ai-application/shared/cloud/aws_provider.py           AWS-native health systems
```

**Status:** Interface + 3 provider stubs (all `NotImplementedError` with TODO + service mappings documented). Default flow (Vertex) is the only one wired end-to-end.

**Why scaffold-not-stubbed-out:** the *abstraction* is the architect signal. Filling Vertex first + Azure/AWS second is a ~2-week project that doesn't change the architecture story. Stub-with-clear-mappings is enough to defend the design in interview.

**To complete:**
- Wire each provider's `embed()`, `vector_search()`, `llm_complete()`, `healthcare_nlp()`, `deidentify()`, `audit_log()` against the cloud-native SDK
- Per-cloud test: `pytest tests/test_vertex_provider.py` etc.
- Per-cloud baseline: re-run Ragas on each, document the deltas

---

## Phase 5 — Integration (⌛ queued — the final lift)

**What:** Wire the 4 services + 2 new apps into a fully integrated system.

**Owner:** AI Platform Architect + GenAI Eng + Architect for cross-app contracts.

**Pieces:**

```
SERVICE / APP                                  WHAT IT BECOMES                              EFFORT
────────────────────────────────────────────────────────────────────────────────────────────────
services/rag-api                               FastAPI wrapping shared/retrieval +          3 days
                                                shared/generate, with /v1/search, /v1/generate
                                                endpoints
services/guardrails-api                        FastAPI wrapping shared/guardrails +         2 days
                                                shared/llama_guard
services/feature-api                           FastAPI consuming Layer 1 ml-pipeline +      4 days
                                                mart_er_triage; /v1/features/{id}
services/analytics-api                         FastAPI consuming Layer 1 mart_operations +  3 days
                                                mart_executive_kpi; /v1/metrics/{name}
apps/ops-capacity-assistant                    Streamlit + multi-step decisioning over     5 days
                                                feature-api + analytics-api
apps/executive-dashboard                       Power BI link + LLM-narrative briefing      3 days
                                                generator (executive_powerbi semantic
                                                model lives in Layer 1)
Eval-on-PR (CI)                                GitHub Actions workflow that runs Ragas +   2 days
                                                red-team on every PR; blocks merge on
                                                regression below baseline
Live data wiring                               Layer 1 gold tables → Layer 2 retrieval     5 days
                                                corpus (replace BM25 with embedding
                                                retrieval — closes context_recall gap)
                                                                                            ───────
                                                                                            ~27 days
                                                                                            (~6 weeks
                                                                                            calendar)
```

---

## ⚠️ Layer 1 honest gaps (audited 2026-05-09)

Earlier docs claimed Layer 1 had things that don't match the code on disk. Logged here so the gap is tracked, not hidden.

```
CLAIM (earlier docs)                       REALITY ON DISK                          STATUS
────────────────────────────────────────────────────────────────────────────────────────────────
3 audience-shaped marts                    ❌ NOT BY THOSE NAMES.                   QUEUED
(mart_er_triage / mart_operations /            Actual SQL is a classic star schema:
 mart_executive_kpi)                            7 dim_*.sql + fact_patient_encounters.sql.
                                                Audience-shaped marts to be built on top.

ML feature: readmission_risk               ⚠️ TRAINING CODE REAL,                   PARTIAL
                                                NEVER PERSISTED.
                                                Target is engineered from
                                                Test Results column ("Abnormal" → 1) =
                                                a PROXY, not real readmission ground truth.
                                                No saved .pkl/.joblib in repo.

ML feature: predicted_los                  ❌ ZERO CODE.                            NOT BUILT
                                                LoS is computed in API as
                                                discharge_date - admission_date subtraction
                                                (arithmetic, not a model).

ML feature: high_utilizer_flag             ❌ ZERO CODE anywhere.                   NOT BUILT
                                                Could be SQL-only (count prior visits > N)
                                                — easy implementation when scheduled.

ML feature: ER_overload_signal             ❌ ZERO CODE anywhere.                   NOT BUILT

ML inference (score.py)                    ❌ PLACEHOLDER.                          NOT BUILT
                                                Mostly commented out; writes hardcoded
                                                dummy CSV ("1,0.85\n2,0.12\n").

PHI redaction at Layer 1                   ❌ NO CODE.                              NOT BUILT
                                                Single grep hit is a markdown comment
                                                about screenshots, not de-id code.
                                                (Layer 2 input_guardrails has spaCy+regex
                                                 PII redaction — that's runtime, not
                                                 data-pipeline level.)

Data-pipeline monitoring                   ❌ NO CODE.                              NOT BUILT
                                                Layer 3 covers AI-output monitoring.
                                                Layer 1 dbt-test-pass-rate / mart-
                                                freshness alerting is queued.
```

**What's defendable in interview today:**
✅ working FastAPI on 55K real synthetic records
✅ professional dbt star schema (14 SQL files, real LAG window for readmission flag)
✅ Power BI TMDL structure (5 tables, 4 relationships — Fabric-dependent at refresh time)
✅ readmission_risk training script (XGBoost+sklearn+MLflow) — with proxy-target caveat
✅ valid OpenAPI 3.1.0 contract with 11 paths

**What's NOT defendable until built:**
❌ predicted_los model · high_utilizer_flag model · ER_overload_signal model
❌ Real ML inference (score.py is a placeholder)
❌ Layer-1-level PHI redaction
❌ Layer-1-level data-pipeline monitoring
❌ Audience-shaped marts (mart_er_triage / mart_operations / mart_executive_kpi)

---

## What "shipped" means in this repo (be honest)

```
✅ shipped         = code exists, runs, has tests, evidence backed by JSON output
⚠️ scaffold        = interface defined, behavior documented, raises NotImplementedError
                    in body but importable + ready to fill
⌛ queued          = explicitly named in Phase 5 above, not yet started
❌ not in scope    = intentionally NOT planned (e.g. K8s, multi-region failover)
```

This taxonomy exists because the worst interview answer is "yes, it's all there" when it isn't. The right answer is *"X is shipped with Y evidence; Z is scaffold; W is queued for Phase 5 with this scoped plan."* That answer is unfailable because it's true.

---

## Cross-references

- **Operational behaviors expected per phase:** [`02_operational_realism.md`](02_operational_realism.md)
- **Layer + role mapping:** [`01_layer_purpose_and_ownership.md`](01_layer_purpose_and_ownership.md)
- **Architecture diagrams:** [`../diagrams/`](../diagrams/)
- **Patient lifecycle (touches Phase 1-3 today, Phase 5 expansion):** [`../docs/05_patient_lifecycle.md`](../docs/05_patient_lifecycle.md)
