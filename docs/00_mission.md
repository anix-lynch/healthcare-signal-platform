# 00 — Mission (the only thing that merges these layers)

> *"Clinical AI that saves lives without getting the hospital sued."*

Every architectural decision in this monorepo answers to one of those two halves. If a feature doesn't make the AI more useful clinically, OR doesn't reduce the chance of a lawsuit, it doesn't ship.

---

## Why mission, not runtime, is the merge

Most enterprise architectures aren't unified by *runtime* — they're unified by *mission*. Microsoft 365 has 50+ products on different stacks (Word's stack ≠ Teams' stack ≠ Power BI's stack), all serving "productivity for knowledge workers." The runtime is downstream of the mission, not the other way around.

This monorepo is the same shape:

```
LAYER 1 — Data Backbone        sub-mission: TRUST THE DATA
                                tools: dbt · Power BI · Fabric · ml-pipeline
                                language: SQL + dbt-Jinja + Python ML
LAYER 2 — AI Application       sub-mission: AI DOES THE WORK
                                tools: 7 patterns · multi-cloud adapter · runtime guardrails
                                language: Python · Pydantic · LLM APIs
LAYER 3 — Governance           sub-mission: AI DOESN'T GO ROGUE
                                tools: Ragas · spaCy · red-team · Llama Guard
                                language: Python eval scripts
```

Three different stacks. Three different languages-of-work. One mission. **That is real architecture, not "I have three repos."**

---

## Sub-mission contracts (what each layer guarantees the next)

### Layer 1 → Layer 2 contract
```
LAYER 1 GUARANTEES               LAYER 2 EXPECTS
─────────────────────────────────────────────────────────────
Clean PHI-redacted patient data  →  Embeddable text rows for retrieval
Stable schema (dbt contracts)    →  No retrieval-breaking field renames
Documented OpenAPI surface       →  Agent-friendly REST endpoints
SLA: silver/gold refresh nightly →  Layer 2 plans for daily-stale data
```

### Layer 2 → Layer 3 contract
```
LAYER 2 GUARANTEES               LAYER 3 EXPECTS
─────────────────────────────────────────────────────────────
Structured Pydantic outputs      →  Schema-validatable for guardrails
Citations on every generation    →  citation_validation can verify
Trace IDs across calls           →  Drift / regression analysis works
Eval harness exposes per-pattern →  Red-team regression CI gates
metrics in JSON                  →  attach to the same baseline files
```

### Layer 3 → Layer 1+2 feedback loop
```
LAYER 3 EMITS                    LAYERS 1+2 CONSUME
─────────────────────────────────────────────────────────────
Drift alerts                     →  Layer 1 retrains/re-ingests
Faithfulness regressions on PR   →  Layer 2 PR blocked, fix before merge
PII redaction-rate reports       →  Layer 1 tightens upstream scrubbing
Adversarial findings             →  Layer 2 hardens prompts / guardrails
```

The feedback loop is what turns a 3-repo "stack" into a learning *system*.

---

## What's shipped vs what's queued (be honest)

```
SHIPPED TODAY
   ✅ Mission alignment (this doc, README hero)
   ✅ Healthcare domain shared (ESI tier, clinical workflow vocabulary)
   ✅ 55K-row corpus → reused by Layer 3 for 200-Q&A eval set
   ✅ Layer 3 PII + red-team logic folded into Layer 2 runtime
   ✅ Eval baselines (Ragas 0.96 / red-team 100% / router 62.2%) backed by JSON

QUEUED — PHASE 5
   ⌛ Layer 1 gold tables → Layer 2 retrieval corpus (live data pipeline)
   ⌛ Layer 3 Ragas → Layer 2 eval-on-PR via GitHub Actions
   ⌛ Unified deployment (Cloud Run / k8s) orchestrating all 3 layers
   ⌛ Single OpenAPI contract surface across layers
   ⌛ Cross-layer trace IDs for end-to-end observability
```

**Don't claim more than is shipped.** When asked "are these really integrated?" the honest answer is:

> "They integrate by mission and design today. The live data pipeline between
>  Layer 1 and Layer 2 is queued for Phase 5. The architecture is real; the
>  wiring is incremental."

That answer is *better* than "yes everything is wired" because it shows the candidate (a) doesn't lie under interview pressure, (b) has a roadmap, (c) understands what shipped means.

---

## Cross-references

- **Top README:** [`../README.md`](../README.md)
- **3-layer title strategy:** [`../../FWD/fail-fwd/possibletitle/3layer_architecture_title_map.md`](../../FWD/fail-fwd/possibletitle/3layer_architecture_title_map.md)
- **Per-layer detail:**
  - [`../layer1-data-backbone/README.md`](../layer1-data-backbone/README.md)
  - [`../layer2-ai-application/README.md`](../layer2-ai-application/README.md)
  - [`../layer3-governance/README.md`](../layer3-governance/README.md)
