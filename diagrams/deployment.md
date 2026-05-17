# Deployment Topology — Multi-Cloud Runtime View

> ASCII deployment diagram for the 3-layer system. Three cloud providers
> shown side-by-side via the `shared/cloud/CloudProvider` adapter.
> The adapter is scaffold-grade today (Vertex wired, Azure/AWS stubbed).

---

## Per-customer deployment shape

Customer picks one CloudProvider via env var; same code runs on all three.

```
                            ┌────────────────────────────────────┐
                            │   CLIENT (charge nurse · ops · CEO) │
                            └─────────────────┬──────────────────┘
                                              │
                                              ▼
                       ╔══════════════════════════════════════════╗
                       ║   🟦 LAYER 1 — DATA BACKBONE              ║
                       ╠══════════════════════════════════════════╣
                       ║                                            ║
                       ║   FastAPI       ←──  api/                  ║
                       ║      ↑                                     ║
                       ║   gold marts    ←──  dbt-project/marts     ║
                       ║      ↑                                     ║
                       ║   silver tables ←──  dbt-project/staging   ║
                       ║      ↑                                     ║
                       ║   bronze raw    ←──  data/raw + checkpoint ║
                       ║      ↑                                     ║
                       ║   source feeds  ←──  EHR · CSV · PDF ·     ║
                       ║                       nurse notes (Phase B) ║
                       ║                                            ║
                       ║   Power BI semantic model ──→ exec dash     ║
                       ║                                            ║
                       ╚══════════════════════╤═════════════════════╝
                                              │  HTTP
                                              ▼
              ╔═════════════════════════════════════════════════════════╗
              ║          🟩 LAYER 2 — AI APPLICATION (apps + services)   ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                         ║
              ║   apps/er-triage           apps/ops-capacity            ║
              ║         │                          │                    ║
              ║         ▼                          ▼                    ║
              ║   ┌──────────────────────────────────────┐              ║
              ║   │  services/rag-api  ◀─── shared/retrieval (Rachel)   ║
              ║   │  services/guardrails-api ─── shared/guardrails      ║
              ║   │  services/feature-api   ─── Layer 1 ml-pipeline     ║
              ║   │  services/analytics-api ─── Layer 1 marts           ║
              ║   └──────────────────────────────────────┘              ║
              ║                       │                                  ║
              ║                       ▼                                  ║
              ║   shared/{classify · regress · generate ·               ║
              ║          anomaly · cluster · rank}                       ║
              ║                       │                                  ║
              ║                       ▼                                  ║
              ║       shared/cloud/CloudProvider (adapter)               ║
              ║   ┌────────────────┬────────────────┬─────────────────┐ ║
              ║   │   Vertex AI    │   Azure OpenAI │     AWS         │ ║
              ║   │   (default)    │   (Microsoft   │   Bedrock       │ ║
              ║   │                │     shop)      │  + SageMaker    │ ║
              ║   └────────────────┴────────────────┴─────────────────┘ ║
              ║                                                         ║
              ╚══════════════════════╤══════════════════════════════════╝
                                     │  (every call wrapped by ↓)
                                     ▼
              ╔═════════════════════════════════════════════════════════╗
              ║              🟥 LAYER 3 — GOVERNANCE                     ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                         ║
              ║   BEFORE AI  PII redact · prompt-injection · token cap  ║
              ║   DURING AI  Pydantic out · tool whitelist · temp cap    ║
              ║   AFTER AI   hallucination · citation valid · Llama Guard║
              ║   OFFLINE    Ragas weekly · red-team 50 · drift monitor  ║
              ║                                                         ║
              ║                       │                                  ║
              ║                       ▼                                  ║
              ║   ┌────────────────────────────────────────────────┐    ║
              ║   │  AUDIT SINK (cross-cloud abstraction)          │    ║
              ║   │   GCP: Cloud Logging                            │    ║
              ║   │   Azure: Application Insights                   │    ║
              ║   │   AWS: CloudWatch                                │    ║
              ║   │   retention: 7 years (HIPAA Safe Harbor min)    │    ║
              ║   └────────────────────────────────────────────────┘    ║
              ║                                                         ║
              ╚═════════════════════════════════════════════════════════╝
```

---

## Per-cloud component mapping

```
COMPONENT (logical)           VERTEX (GCP)            AZURE                AWS
─────────────────────────────────────────────────────────────────────────────────────
warehouse                     BigQuery                Synapse / Fabric     Redshift
object store                  Cloud Storage           Blob Storage         S3
vector DB                     Vertex Vector Search    Azure AI Search      OpenSearch
LLM inference                 Vertex Model Garden     Azure OpenAI         Bedrock
embedding endpoint            text-embedding-005      text-embedding-3     Titan Embeddings
API runtime                   Cloud Run               Container Apps       App Runner / ECS
auth                          Workload Identity       Managed Identity     IAM roles
audit sink                    Cloud Logging           Application Insights CloudWatch
secrets                       Secret Manager          Key Vault             Secrets Manager
PII NER (clinical)            Vertex Healthcare NLP   Text Analytics Health Comprehend Medical
de-identify                   Healthcare API DICOM    HCAPI / Purview      Comprehend Medical
```

---

## Honest scope today (NOT prod-deployed)

```
SHIPPED (in repo, runs locally)
   ✅ FastAPI api/ with 11 endpoints
   ✅ dbt-project/ with staging + marts (Fabric-targeted today)
   ✅ shared/* patterns importable, smoke-tested
   ✅ scripts/checkpoint.py gate before mart release
   ✅ Vertex AI enrichment path (uses GCP $900 credit)

SCAFFOLD (interface exists, body raises NotImplementedError)
   ⚠️ shared/cloud/azure_provider.py
   ⚠️ shared/cloud/aws_provider.py
   ⚠️ services/* FastAPI shells (rag-api, guardrails-api, feature-api, analytics-api)

NOT DEPLOYED (would be Phase 5 — actual runtime hosting)
   ❌ Cloud Run / Container Apps / App Runner runtime
   ❌ event-driven orchestration (PubSub / Event Grid / EventBridge)
   ❌ vector DB hosting (today retrieval is in-memory BM25)
   ❌ unified audit sink wired across providers
   ❌ HIPAA BAA execution (architectural design only)
```

---

## Failure modes (cross-ref)

See [`../docs/failure_modes.md`](../docs/failure_modes.md) for the 10 named
failure modes the architecture handles + the guards that fire on each.

---

## Why this matters

```
Thin slice:    "I built one service."
                Reader: "OK, what about the other 11?"

System view:   "Here's the 3-layer topology, the per-cloud component
                 map, the guards, the failure modes, and the deferred-
                 vs-shipped honesty boundary."
                Reader: "Tell me about the trade-offs you made."
```

The second conversation is the one this document optimizes for.
