"""Pattern 1 — Rachel public API."""
from .baseline import retrieve, retrieve_for_case, Method
from .schema import RachelOutput, Hit, HitType, RetrievalMethod
from .guardrails import (
    RetrievalGuardError,
    validate_citations,
    filter_cross_patient,
    enforce_score_floor,
    apply_all_guards,
)
from .retriever import search, search_for_case, index_cases, index_size
from . import dense

__all__ = [
    "retrieve",
    "retrieve_for_case",
    "Method",
    "RachelOutput",
    "Hit",
    "HitType",
    "RetrievalMethod",
    "RetrievalGuardError",
    "validate_citations",
    "filter_cross_patient",
    "enforce_score_floor",
    "apply_all_guards",
    "search",
    "search_for_case",
    "index_cases",
    "index_size",
    "dense",
]
