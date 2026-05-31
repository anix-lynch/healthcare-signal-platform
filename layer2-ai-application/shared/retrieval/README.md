# Pattern 1 — retrieval 🔍

> **"bro find me another patient who almost died like this 😭"**

This is retrieval. NOT classification (that's classifier). NOT regression
(that's forecast). NOT generation (that's generation).

retrieval answers ONE question:

```
"what does this remind me of?"
```

She returns the K most similar past cases + the relevant guidelines.
generation then grounds every generated claim on a `source_id` from retrieval.
Without retrieval, every downstream chart note hallucinates.

---

## Why she sits here

Every L2 app that summarises, decides, or briefs needs to cite something:

```
the triage app (broader platform)              → cite similar past triages on escalation rationale
the ops app (broader platform) → cite similar past LoS patterns for routing
the exec app (broader platform)    → cite KPI guidelines + past briefings
services/rag-api            → wraps retrieval as /v1/search
shared/generate   → consumes retrieval hits as grounding context
```

Five callers, one engine. That's why retrieval lives in `shared/`, not inside
any one app folder.

---

## File map

```
shared/retrieval/
├── __init__.py        public API (retrieve, retrievalOutput)
├── schema.py          Pydantic output contract — Hit + retrievalOutput
├── baseline.py        orchestrator (method="bm25"|"dense") → retrievalOutput
├── retriever.py       BM25 engine — token-overlap floor
├── dense.py           sentence-transformers MiniLM cosine — semantic layer
├── guardrails.py      citation validation + cross-patient leak + score floor
├── identity.py        patient_id resolver (Layer 1 identity map, optional)
├── eval.py            Recall@K / Precision@K / MRR / NDCG / ClinicalRecall@K
└── README.md          you are here
```

---

## What's shipped vs what's stub

```
COMPONENT                     STATUS         NOTES
─────────────────────────────────────────────────────────────────────────────
BM25 search                   ✅ shipped     pure Python, 55K corpus
search_for_case               ✅ shipped     builds query from case dict
schema (retrievalOutput / Hit)   ✅ shipped     pydantic, matches /v1/search shape
citation validation           ✅ shipped     drops unresolved source_ids
cross-patient leak filter     ✅ shipped     wired via identity.patient_of;
                                              degrades to no-op when L1 map
                                              missing (warns, doesn't crash)
score-floor guard             ✅ shipped     drops sub-threshold junk
Recall/Precision/MRR/NDCG     ✅ shipped     needs golden set to run
ClinicalRecall@K              ✅ shipped     ceiling metric — pass via
                                              evaluate(..., bucket_of=fn)
dense embedding retrieval     ✅ shipped     MiniLM, method="dense" with
                                              BM25 fallback if encoder missing
hybrid (BM25 + dense + RRF)   ❌ queued      reciprocal rank fusion
cross-encoder rerank          ❌ queued      ms-marco-MiniLM, optional layer
```

**Do not claim production-grade retrieval.** Current implementation is
BM25 over row-rendered snippets from a 15-column billing registry. Dense
+ hybrid + rerank are scoped, not shipped.

---

## The brutal mantra

```
BM25 alone =  "this word appeared in both"
DENSE alone = "this concept appeared in both"
HYBRID =      "both checks agreed"
RERANK =      "now a smarter model re-orders the top-50"

production retrieval = HYBRID + RERANK
demo retrieval =       BM25 with guards
current retrieval =       demo retrieval, honestly labeled
```

A model that does dense + hybrid + rerank but loses to BM25 + guards on
Recall@10 is broken, not impressive. Eval gate first, fancy retrieval second.

---

## Two query modes you must internalize

```
QUERY-TO-ITEM    embed(user_text) → top-K past cases
                 retrieve("62yo M chest pain")
                 → list of similar cases

ITEM-TO-ITEM     embed(anchor_case) → top-K similar cases
                 retrieve_for_case(case_dict, k=5)
                 → "more like this" / "what else looks like CASE-104"
```

Same engine. Same math. Different UX. TikTok's For You = item-to-item.
YouTube's search bar = query-to-item. ER use cases need both.

---

## Healthcare meaning

```
CASE                                RACHEL OUTPUT
─────────────────────────────────   ──────────────────────────────────
62yo M, chest pain, ambulance       top-K similar past chest-pain admits
                                    + chest-pain ESI guideline
                                    + protocol for cardiac workup

MJ video "Man in the Mirror live"   top-K similar live performance videos
                                    + lyric ↔ performance crosswalk
                                    (different domain, same Pattern 1)
```

retrieval doesn't care about the domain. She cares about "what reminds me
of what." Hospital chaos or pop catalog — same engine.

---

## Why retrieval ≠ classification (the line that gets confused)

```
RACHEL (retrieval)          TRAFFIC LIGHT (classification)
output: list of items       output: discrete bucket
"what reminds me of?"       "which bucket does this go in?"
metric: Recall@K, NDCG      metric: F1, precision, recall (per class)
failure: missed relevant    failure: misrouted to wrong tier
                            
Together:
  retrieval surfaces context  →  classifier decides urgency
  retrieval: "this smells like past cardiac near-death ghosts"
  classifier: "cool, then NOW — move 😭"
```

---

## Senior architect during hospital chaos — the tone we keep

```
BAD                                GOOD
─────────────────────────────      ─────────────────────────────────────
"found cool similar stuff lol"     "5 hits returned, Recall@10 = 0.74,
                                     1 dropped via score floor"
"ai vibes the right answer"        "retrieval_method=bm25_fallback,
                                     embedding service degraded at 14:03"
"100% match"                       "similarity 0.82, source resolved,
                                     same-patient leak filtered (n=1)"
```

The hit can be uncertain. The framing cannot.

---

## Quick start

```python
from shared.retrieval import retrieve, retrieve_for_case

# query-to-item
out = retrieve("62yo M chest pain diaphoresis", query_case_id="Q-001", k=5)
print(out.model_dump_json(indent=2))

# item-to-item
case = {"cc": "chest pain", "hpi": "62yo M, substernal pressure 30 min"}
out = retrieve_for_case(case, query_case_id="CASE-104", k=5)
```

Output:

```json
{
  "pattern": "rachel_retrieval",
  "query_case_id": "Q-001",
  "retrieved": [
    {
      "source_id": "L1-002150",
      "type": "past_case",
      "similarity": 0.86,
      "summary": "62yo Male, Hypertension, Emergency admission, treated with Aspirin",
      "why_relevant": "shared tokens: chest, hypertension, emergency"
    }
  ],
  "retrieval_method": "bm25",
  "fallback_used": false,
  "latency_ms": 47,
  "warnings": []
}
```

---

## Eval harness

```python
from shared.retrieval.eval import evaluate
from shared.retrieval import retrieve

def retriever_fn(query: str, k: int) -> list[str]:
    return [h.source_id for h in retrieve(query, k=k).retrieved]

golden = [
    {"query_id": "Q-001",
     "query_text": "62yo M chest pain hypertension",
     "relevant_ids": ["L1-002150", "L1-040201"],
     "graded_relevance": {"L1-002150": 3, "L1-040201": 2}},
]

report = evaluate(golden, retriever_fn, k_values=(1, 5, 10))
print(report)
# {"n_queries": 1, "recall@1": ..., "recall@5": ..., "mrr": ..., "ndcg@10": ...}
```

---

## Roadmap (when richer data arrives)

```
NOW (registry_v1)              BM25 over 15-col rendered snippets
                               retrieval_method = "bm25"
                               warnings = "no dense — registry-only data"

NEXT (registry_v2_enriched)    BM25 over CC+HPI+physician_note
                               + sentence-transformers dense
                               retrieval_method = "hybrid_bm25_dense"

REAL (real EHR)                hybrid + cross-encoder rerank
                               cross-patient lookup wired to patient_id
                               retrieval_method = "hybrid+rerank"
```

---

## Cross-references

- Repo overview: `../../../README.md`
- Sibling patterns: `../classify/`, `../regress/`
