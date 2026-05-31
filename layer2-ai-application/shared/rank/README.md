# Pattern 7 — ranking 👮

> **"which evidence should appear first 😭"**

Reranks retrieval's top-K hits. The smaller, sharper lineup that generation
grounds against. retrieval cares about RECALL. ranking cares about
which hit lands FIRST.

## File map

```
shared/rank/
├── __init__.py        public API (lineup, PoliceLineupOutput, RankedHit)
├── schema.py          Pydantic output contract
├── baseline.py        wraps reranker.rerank() → PoliceLineupOutput
├── reranker.py        heuristic severity + age/condition engine (existing)
└── README.md          you are here
```

## What's shipped

```
heuristic rerank              ✅ shipped (age + condition + severity signals)
top_k cut                     ✅ shipped (default 5)
original_rachel_rank tracking ✅ shipped (enables NDCG lift math)
cross-encoder rerank          ❌ queued (ms-marco-MiniLM)
NDCG lift vs retrieval offline   ❌ queued — populates ndcg_lift_vs_rachel field
ensemble (heuristic + xenc)   ❌ queued
```

## The brutal mantra

```
no rerank   = retrieval's order is the order
heuristic   = re-promote severity-matching hits to the top
cross-enc   = small LLM re-reads each hit vs query, scores
ensemble    = both, weighted

production rank gate: NDCG@5 with heuristic > retrieval raw on holdout
if it loses → ship retrieval raw, the rerank is theater
```

## Together with the other patterns

```
retrieval:        top-50 candidate hits
ranking: top-5 reranked, sharper
generation:       grounds chart note on those 5 (citations)
anomaly detector: checks the SAME 5 — if they're in weird cluster, flag review
```

## Quick start

```python
from shared.retrieval import retrieve
from shared.rank import lineup

rachel = retrieve("62yo M chest pain hypertension", k=20)
out = lineup(
    query="62yo M chest pain hypertension",
    candidates=[h.model_dump() for h in rachel.retrieved],
    case_id="CASE-104",
    top_k=5,
)
print(out.model_dump_json(indent=2))
```
