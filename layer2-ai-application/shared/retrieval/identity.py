"""
Pattern 1 — Rachel · Patient identity bridge.

Loads Layer 1's patient_identity_map.json (encounter_id → patient_id) and
exposes a `patient_of(case_id) → str | None` callable that Rachel's
cross-patient leak guard consumes.

Why this lives in shared/retrieval/:
    Strictly, Layer 1 owns identity resolution. But pulling the JSON via
    a Python import is the cheapest way to wire the guard for the current
    demo. When the FastAPI in layer1-data-backbone/api/ exposes
    /v1/patient_of/{encounter_id}, swap this module's implementation to
    an HTTP call without touching baseline.py.

Why JSON not in-process import:
    Generation lives in scripts/patient_identity.py and writes one file.
    Retrieval reads that file once at module init. Decoupled, swap-friendly.

Honest failure mode:
    If the map JSON is missing, the cross-patient guard becomes a no-op
    (returns None for every source_id). We log a warning once. This is the
    same behavior as before the bridge existed — degraded, not broken.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional

_LOG = logging.getLogger(__name__)

# Resolve the path the same way los_predictor + retriever do.
_DEFAULT_MAP = (
    Path(__file__).resolve().parents[3]
    / "layer1-data-backbone" / "data" / "derived" / "patient_identity_map.json"
)


class _IdentityCache:
    """Lazy-loaded singleton wrapping the encounter_to_patient dict."""

    def __init__(self):
        self._loaded: bool = False
        self._enc_to_pat: dict[str, str] = {}
        self._stats: dict = {}
        self._warning_logged: bool = False
        self._path: Path = _DEFAULT_MAP

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._path.exists():
            if not self._warning_logged:
                _LOG.warning(
                    "patient_identity_map.json missing at %s — "
                    "cross-patient guard will be a no-op. "
                    "Run scripts/patient_identity.py in layer1-data-backbone to generate.",
                    self._path,
                )
                self._warning_logged = True
            return
        with self._path.open() as f:
            payload = json.load(f)
        self._enc_to_pat = payload.get("encounter_to_patient", {})
        self._stats = payload.get("stats", {})
        _LOG.info(
            "loaded patient identity map: %d encounters across %d patients",
            self._stats.get("n_encounters", 0),
            self._stats.get("n_unique_patients", 0),
        )

    def patient_of(self, case_id: str) -> Optional[str]:
        self._load()
        return self._enc_to_pat.get(case_id)

    def stats(self) -> dict:
        self._load()
        return dict(self._stats)


_CACHE = _IdentityCache()


def patient_of(case_id: str) -> Optional[str]:
    """Return the stable patient_id for an encounter_id, or None if unknown."""
    return _CACHE.patient_of(case_id)


def identity_stats() -> dict:
    """Diagnostic — counts, top repeaters, etc. Loads map if not yet loaded."""
    return _CACHE.stats()


def is_available() -> bool:
    """True iff the map JSON loaded successfully and has entries."""
    _CACHE._load()
    return bool(_CACHE._enc_to_pat)


# Public alias — preferred name for cross-module callers.
identity_available = is_available
