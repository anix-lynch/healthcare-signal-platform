"""Pattern 1 — Rachel (Retrieval) | seven-lens

ER context: "Find me past ER cases that smell like this chief complaint."
GenAI lens: embeddings + ANN (FAISS/HNSW) + hybrid BM25 fallback.

Eval metrics live in app/evaluation/retrieval_eval.py:
    Precision@K · NDCG · Recall@K

Note: ER2 already ships a working version of this. ER3's copy is for
local eval harness wiring. In production use either:
    - `pip install -e ../ER2` and `from er2.app.retrieval import search`
    - HTTP call to ER2's deployed Cloud Run service
"""

from typing import Iterable


def search(query: str, k: int = 10) -> list[dict]:
    """Return top-k cases ranked by semantic similarity to query.

    Returns:
        List of {case_id, score, snippet} dicts, length <= k.
    """
    raise NotImplementedError("TODO: wire to ER2 retrieval module or local FAISS index")


def index_cases(cases: Iterable[dict]) -> None:
    """Build/update the embedding index from a corpus of cases."""
    raise NotImplementedError("TODO: embed + upsert to FAISS / Chroma / Vertex Vector Search")
