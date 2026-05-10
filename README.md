# healthcare-genai-fullstack

> A 3-layer enterprise GenAI architecture for clinical AI: trusted data → AI reasoning → governance. Mission-coherent, monorepo-organized, multi-cloud-deployable. Built pain-driven, retroactively coherent — the way real architects actually emerge.

---

## 🎯 The Mission (the only thing that merges these layers)

```
"Clinical AI that saves lives without getting the hospital sued."

LAYER 1   trust the data        (so AI isn't reasoning on garbage)
LAYER 2   AI does the work      (so a clinician gets a fast triage suggestion)
LAYER 3   AI doesn't go rogue   (so the hospital's lawyer sleeps at night)

       ▼  rolls up to  ▼

  SAVE LIVES + DON'T GET SUED.
```

This is the binding force. Each layer is independently deployable, written in
the right tool for its job (dbt for data, Python for AI, eval scripts for
governance). They merge by mission, not by runtime. That is what real
enterprise architectures look like.

---

## 🧱 The 3-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  REAL HOSPITAL WORLD (chaos)                                         │
│  EHR · EMR · PDFs · CSVs · billing · schedules · policies            │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
══════════════════════════════════════════════════════════════════════════
🟦 LAYER 1 — DATA BACKBONE                  layer1-data-backbone/
══════════════════════════════════════════════════════════════════════════
   "trust the data"

   BRONZE  raw chaos                  →  data/raw/
   SILVER  cleaned · deduped · PHI-redacted  →  dbt-project/staging
   GOLD    business-ready marts + ML  →  dbt-project/marts + ml-pipeline
   BEYOND  semantic + Power BI + API  →  powerbi-model + api/openapi
══════════════════════════════════════════════════════════════════════════
                           │
                           │  "AI can chew on this"
                           ▼
══════════════════════════════════════════════════════════════════════════
🟩 LAYER 2 — AI APPLICATION                 layer2-ai-application/
══════════════════════════════════════════════════════════════════════════
   "AI does the work"

   7 PATTERNS  retrieval · classify · regress · generate · anomaly ·
               cluster · rank
   MULTI-CLOUD CloudProvider adapter — same code on Vertex / Azure / AWS
   GUARDRAILS  input + output runtime layer (folded in)
   MEMORY      3-tier (short-term · session · long-term)
   EVAL        per-pattern harness (P@K · F1 · MAE · faithfulness · etc.)
══════════════════════════════════════════════════════════════════════════
                           │
                           │  "but watch the AI"
                           ▼
══════════════════════════════════════════════════════════════════════════
🟥 LAYER 3 — GOVERNANCE                      layer3-governance/
══════════════════════════════════════════════════════════════════════════
   "AI doesn't go rogue"

   BEFORE AI  input sanitize · prompt-injection · PII redact · token limit
   DURING AI  constrained generation · structured output · tool-use rules
   AFTER AI   hallucination check · citation validation · forbidden actions
   OFFLINE    Ragas eval · 50-prompt red-team corpus · regression gates
══════════════════════════════════════════════════════════════════════════
```

---

## 📊 Real Numbers (JSON-backed in each layer)

```
🎯 ACCURACY
   Ragas faithfulness                   0.958
   Ragas answer_relevancy               0.856
   Ragas context_recall                 0.128 ⚠️ tracked gap (BM25 weak; embedding fix queued)
   n samples                            50
   judge / generator                    Claude Haiku (via OpenRouter)
   evidence                             layer3-governance/data/ragas_healthcare_results.json

💰 COST
   3-tier model router                  62.2% cost reduction vs GPT-4o
   tier distribution                    32% Haiku · 52% Gemini Flash · 16% Sonnet
   evidence                             layer3-governance/data/router_results.json

🛡️ COMPLIANCE
   PII tokens redacted                  1,753 (regex + spaCy NER)
   red-team block rate                  100% across 5 attack categories (50 prompts)
   evidence                             layer3-governance/data/redteam_block_rate.json

🤖 INNOVATION
   Patterns codified                    7 (under one universal eval harness)
   Cloud providers supported            3 (Vertex · Azure · AWS via single adapter)
   Layers separated                     3 (data · app · governance — visible in folder layout)

🌟 OUTCOME (engineer-attributable)
   Real corpus prepared                 55,000 synthetic patient records (Layer 1)
   Adversarial test corpus              50 prompts, 5 attack categories (Layer 3)
   Eval harness reproducibility         every metric backed by a JSON output file
```

---

## 📁 Repo Map

```
healthcare-genai-fullstack/
│
├── README.md                          ← you are here (3-layer hero)
├── Makefile                           ← top-level: orchestrates per-layer
├── docs/                              ← architecture · mission · runbooks
│
├── layer1-data-backbone/              🟦 dbt + Power BI + Fabric + ml-pipeline
│   ├── data/raw/                      55K-row synthetic patient dataset
│   ├── dbt-project/                   medallion architecture (bronze/silver/gold)
│   ├── powerbi-model/                 semantic model + DAX
│   ├── ml-pipeline/                   MLflow + LoS regression prototype
│   ├── api/                           FastAPI + OpenAPI contract
│   └── README.md
│
├── layer2-ai-application/             🟩 lean apps + services + shared (restructured 2026-05-09)
│   ├── apps/                          ← WHO consumes (audience-shaped)
│   │   ├── er-triage/                    clinicians (NOW / SOON / WAIT)
│   │   ├── ops-capacity-assistant/       ops team — Phase 5 stub
│   │   └── executive-dashboard/          execs — Phase 5 stub
│   │
│   ├── services/                      ← WHAT powers them (HTTP APIs — Phase 5 stubs)
│   │   ├── rag-api/                      retrieval + generation
│   │   ├── guardrails-api/               input + output safety
│   │   ├── feature-api/                  per-patient ML features (from Layer 1)
│   │   └── analytics-api/                system-state KPIs (from Layer 1)
│   │
│   └── shared/                        ← the 7 patterns + cross-cutting libs
│       ├── retrieval/                 Pattern 1 — Rachel
│       ├── classify/                  Pattern 2 — Traffic Light + 3-tier router
│       ├── regress/                   Pattern 3 — Crystal Ball
│       ├── generate/                  Pattern 4 — Mad Lib
│       ├── anomaly/                   Pattern 5 — Smoke Detector
│       ├── cluster/                   Pattern 6 — Treasure Map
│       ├── rank/                      Pattern 7 — Police Lineup
│       ├── guardrails/                input + output runtime layer
│       ├── memory/                    3-tier memory (short · session · long-term)
│       ├── evaluation/                per-pattern eval harness
│       └── cloud/                     CloudProvider adapter (Vertex/Azure/AWS)
│
│   (er-triage-specific bits live INSIDE apps/er-triage/:
│    classify/esi_classifier.py · safety/safety_agent.py · inputs/golden_esi.json ·
│    outputs/baseline/{ragas,redteam,router}_baseline.json · tests/red_team/)
│
└── layer3-governance/                 🟥 eval + safety + red-team
    ├── scripts/
    │   ├── 01_gen_healthcare_qa.py    Q&A benchmark generator
    │   ├── 02_run_ragas_healthcare.py Ragas faithfulness + relevancy
    │   ├── 03_classifier_router.py    3-tier cost router
    │   ├── 04_pii_masker.py           regex + spaCy PII redaction
    │   ├── 05_llama_guard.py          Vertex Llama Guard secondary safety
    │   └── 06_redteam_suite.py        50-prompt adversarial corpus
    ├── data/                          baseline JSONs (every claim has evidence)
    └── README.md
```

---

## 🚀 Quick Start

```bash
# Layer 2 (AI app) is the primary runtime — most users start here
cd layer2-ai-application
pip install -r requirements.txt
make eval-all              # run all 7 pattern evals against golden set
make redteam-test          # regression gate: red-team must hold 100% block rate

# Layer 1 (data) — for the dbt + Power BI side
cd ../layer1-data-backbone
# (see layer's own README — Fabric / dbt / Power BI workflow)

# Layer 3 (governance) — for re-running eval baselines
cd ../layer3-governance
python scripts/02_run_ragas_healthcare.py
python scripts/06_redteam_suite.py
```

---

## 🎯 The Architect/Junior Line (the interview moment)

```
JUNIOR  thinks   →   "LLM = whole system"
                      (one repo, monolith, AI is the product)

ARCHITECT thinks →   "LLM = ONE DANGEROUS COMPONENT inside a bigger system"
                      (data + app + governance — three layers, one mission)
```

You can scroll the folder tree above and SEE which mindset built this repo.
That's the signal. Mission first. Layers next. Runtime integration as it
earns its way in.

---

## 🛠️ How the layers actually integrate (today vs designed)

```
TYPE OF MERGE       STATUS    DETAIL
─────────────────────────────────────────────────────────────────────────────
MISSION             ✅ NOW    "save lives + don't get sued" binds all 3
DOMAIN              ✅ NOW    Healthcare ontology shared (ESI tier, clinical workflow)
DATA                ⚠️ PART   Layer 1's 55K corpus → Layer 3's 200-Q&A eval set ✓
                              Layer 1 gold tables → Layer 2 retrieval corpus ⌛ Phase 5
GUARDRAIL RUNTIME   ✅ NOW    Layer 3 PII + red-team folded into Layer 2 runtime
EVAL CONTRACT       ✅ NOW    Layer 3 baselines guard Layer 2 PRs (regression gates)
DEPLOYMENT          ❌ Phase5 Each layer deploys independently today; unified k8s/Cloud Run
                              orchestration is queued
```

That row 3 (DATA) and row 7 (DEPLOYMENT) are honest gaps. **Don't claim more
than is shipped.** When asked: "they integrate by mission and design today;
the live data pipeline between Layer 1 and Layer 2 is queued for Phase 5."

---

## 🧭 Cross-references

- **Title-to-layer map:** [`fail-fwd/possibletitle/3layer_architecture_title_map.md`](file:///Users/anixlynch/dev/FWD/fail-fwd/possibletitle/3layer_architecture_title_map.md)
- **Role-KPI tree:** [`fail-fwd/possibletitle/genai_role_kpi_trees.md`](file:///Users/anixlynch/dev/FWD/fail-fwd/possibletitle/genai_role_kpi_trees.md)
- **Cookie-cutter framework:** [`fail-fwd/cookiecutter_by_role.md`](file:///Users/anixlynch/dev/FWD/fail-fwd/cookiecutter_by_role.md)
- **6-pillar Nora Bing:** [`mj/docs/nora_bing_metric.md`](file:///Users/anixlynch/dev/mj/docs/nora_bing_metric.md)

---

*Consolidated 2026-05-09 from three independently-evolved repos that turned out
to be three layers of one enterprise GenAI architecture all along. Pain-driven,
mission-coherent, retroactively visible. The way real architects actually emerge.*
