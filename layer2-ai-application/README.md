# Layer 2 — AI Application Layer

> **Lean enterprise structure (2026-05-09 restructure):** apps consume by audience. services expose APIs. shared holds the reusable patterns. Three groups, no sprawl.

---

## 🧩 The shape

```
layer2-ai-application/
│
├── apps/                          ← WHO consumes (audience-shaped)
│   ├── er-triage/                    clinicians  (NOW / SOON / WAIT)
│   ├── ops-capacity-assistant/       ops team    (bed pressure · staffing · routing)
│   └── executive-dashboard/          execs       (KPI briefings · narrative)
│
├── services/                      ← WHAT powers them (HTTP APIs)
│   ├── rag-api/                      retrieval + generation + grounded eval
│   ├── guardrails-api/               input + output runtime safety
│   ├── feature-api/                  per-patient ML feature serving (from Layer 1)
│   └── analytics-api/                system-state KPI serving (from Layer 1)
│
├── shared/                        ← the 7 GenAI patterns + cross-cutting libs
│   ├── retrieval/                    Pattern 1 — Rachel
│   ├── classify/                     Pattern 2 — Traffic Light (3-tier router)
│   ├── regress/                      Pattern 3 — Crystal Ball
│   ├── generate/                     Pattern 4 — Mad Lib
│   ├── anomaly/                      Pattern 5 — Smoke Detector
│   ├── cluster/                      Pattern 6 — Treasure Map
│   ├── rank/                         Pattern 7 — Police Lineup
│   ├── guardrails/                   input + output + Llama Guard runtime
│   ├── memory/                       3-tier memory (short · session · long-term)
│   ├── cloud/                        multi-cloud adapter (Vertex · Azure · AWS)
│   └── evaluation/                   per-pattern eval harness
│
├── Makefile                       (delegates to apps/er-triage's Makefile)
└── requirements.txt
```

---

## 🎯 Title-to-folder map (recruiter pointing)

```
ROLE                           POINT FIRST AT
────────────────────────────────────────────────────────────────────────
Applied AI Engineer            apps/er-triage/  +  shared/  (the 7 patterns)
GenAI Engineer                 apps/er-triage/  +  shared/
Forward Deployed Engineer      apps/er-triage/  ("real product, real data")
GenAI Platform Architect       services/  +  shared/cloud  (API surface story)
AI Platform Engineer           services/  +  ../layer3-governance/
AI Workflow Engineer           apps/ops-capacity-assistant  (multi-step decisioning)
AI Solutions Architect         WHOLE LAYER + cross-app integration
AI Technical Consultant        ALL 3 LAYERS (data backbone · this layer · governance)
```

The lean shape = recruiter clicks ONE folder and gets the role-specific story in 30 seconds.

---

## 🔧 Real numbers (folded from healthcare-rag-guardrails)

```
🎯 ACCURACY     faithfulness 0.958 · relevancy 0.856 · context_recall 0.128 ⚠️
                evidence: apps/er-triage/outputs/baseline/ragas_baseline.json

💰 COST         62.2% reduction vs GPT-4o via 3-tier router (Haiku/Flash/Sonnet)
                evidence: apps/er-triage/outputs/baseline/router_baseline.json

🛡️ COMPLIANCE   1,753 PII tokens redacted · 100% red-team block (50 prompts)
                evidence: apps/er-triage/outputs/baseline/redteam_baseline.json
```

---

## 🚦 Status

```
SHIPPED
   ✅ apps/er-triage scaffold (7 patterns + safety + ESI classifier)
   ✅ shared/ — 10 modules · real Ragas + real PII masker + Llama Guard
   ✅ Eval harness + JSON-backed baselines
   ✅ Multi-cloud CloudProvider (Vertex / Azure / AWS)
   ✅ Red-team regression gate

STUB / SCAFFOLD
   ⚠️ apps/ops-capacity-assistant — README only (Phase 5)
   ⚠️ apps/executive-dashboard — README only (Phase 5)
   ⚠️ services/* — READMEs only (FastAPI impl is Phase 5)

QUEUED — PHASE 5
   ⌛ services/rag-api · guardrails-api · feature-api · analytics-api implementations
   ⌛ ops-capacity-assistant + executive-dashboard apps
   ⌛ Eval-on-PR via GitHub Actions
```

---

## 🎬 Quick start

```bash
cd apps/er-triage
make eval-all                 # run all 7 pattern evals against golden set
make redteam-test             # red-team must hold 100% block rate
make smoke                    # Phase 2 ESI auto-tag smoke test
```

Or from this layer's root: `make eval-all` (delegates to apps/er-triage).

---

## 📚 Cross-references

- **Top-level mission:** [`../README.md`](../README.md) · [`../docs/00_mission.md`](../docs/00_mission.md)
- **Layer 1 (data backbone):** [`../layer1-data-backbone/`](../layer1-data-backbone/)
- **Layer 3 (governance):** [`../layer3-governance/`](../layer3-governance/)
- **Per-app docs:** `apps/*/README.md`
- **Per-service docs:** `services/*/README.md`
- **er-triage detailed docs:** [`apps/er-triage/docs/`](apps/er-triage/docs/)
