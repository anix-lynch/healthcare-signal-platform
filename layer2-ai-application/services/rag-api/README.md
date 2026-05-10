# rag-api

> **Status:** scaffold
> **Wraps:** `shared/retrieval` (Rachel pattern) + `shared/generate` (Mad Lib pattern) + `shared/evaluation` (P@K · NDCG · faithfulness)
> **Consumed by:** `apps/er-triage` · future apps that need grounded generation

---

## Purpose

Single HTTP surface for "retrieval-augmented generation" so apps don't reach into shared libs directly. Apps stay thin; the RAG complexity lives behind one API.

## Endpoints (planned)

```
GET  /search?query=...&k=10            → top-k retrieved cases
                                          (uses shared/retrieval/retriever.py)

POST /generate                          → grounded generation with citations
     body: {query, retrieved, schema}     (uses shared/generate/chart_note.py
                                           + cite-or-refuse guard)

POST /eval                              → run Ragas eval on a Q&A set
     body: {qa_pairs}                    (uses shared/evaluation/{retrieval,generate}_eval.py)

GET  /baselines                         → return current eval baselines
                                          (faithfulness 0.96, P@K, NDCG, etc.)
```

## Why this is a service, not just a library

Apps consume retrieval+generation as a UNIT. Doing them separately leads to citation drift (retrieve A, generate from B). Wrapping the pair behind one API enforces:
- citation-source consistency
- structured output schema validation
- automatic eval-on-call (sample request to Ragas pipeline)
- single auth/audit surface

## Phase 5 implementation notes

- FastAPI server, OpenAPI auto-published
- CloudProvider-aware via `shared/cloud/factory.py` (env-var swap)
- Wired into `services/guardrails-api` for input/output safety pipeline
- Trace ID propagation across retrieval+generation calls
