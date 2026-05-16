"""
CROSS-PATIENT LEAK guard (Pattern 1 — Rachel).

Bobby has 4 prior ER visits in our registry. When we retrieve similar past
cases for Bobby's current visit, we must NOT return Bobby's own old rows —
that's the readmission_history feature, not retrieval.

Verifies:
  - filter_cross_patient drops same-patient hits, keeps other patients
  - the guard is a no-op when query has no patient_id
  - baseline.retrieve() warns when patient_id given but identity map missing
  - apply_all_guards records suppression count in warnings
"""
from __future__ import annotations
import sys
import pathlib

ER_TRIAGE = pathlib.Path(__file__).resolve().parents[1]
LAYER2_ROOT = ER_TRIAGE.parent.parent
sys.path.insert(0, str(LAYER2_ROOT))

from shared.retrieval.guardrails import filter_cross_patient, apply_all_guards
from shared.retrieval.schema import Hit, RachelOutput


def _h(source_id: str, sim: float = 0.8) -> Hit:
    return Hit(
        source_id=source_id,
        type="past_case",
        similarity=sim,
        summary=f"snippet for {source_id}",
        why_relevant="test",
    )


# ── filter_cross_patient ───────────────────────────────────────────────────
def test_filter_drops_same_patient_keeps_others():
    hits = [_h("L1-000100"), _h("L1-000101"), _h("L1-000102"), _h("L1-000103")]
    # Bobby owns L1-000100 and L1-000102; Alice owns the rest.
    owner = {
        "L1-000100": "PT-Bobby",
        "L1-000101": "PT-Alice",
        "L1-000102": "PT-Bobby",
        "L1-000103": "PT-Charlie",
    }
    kept, dropped = filter_cross_patient(
        hits,
        query_patient_id="PT-Bobby",
        hit_patient_of=lambda sid: owner.get(sid),
    )
    kept_ids = {h.source_id for h in kept}
    assert dropped == 2
    assert "L1-000100" not in kept_ids
    assert "L1-000102" not in kept_ids
    assert kept_ids == {"L1-000101", "L1-000103"}


def test_filter_noop_when_query_has_no_patient_id():
    hits = [_h("L1-000100"), _h("L1-000101")]
    kept, dropped = filter_cross_patient(
        hits,
        query_patient_id=None,
        hit_patient_of=lambda sid: "PT-Bobby",
    )
    assert dropped == 0
    assert len(kept) == 2


def test_filter_keeps_hit_when_patient_unknown():
    """If we can't resolve a hit's patient, we keep it — degraded, not strict."""
    hits = [_h("L1-000100"), _h("L1-000101")]
    kept, dropped = filter_cross_patient(
        hits,
        query_patient_id="PT-Bobby",
        hit_patient_of=lambda sid: None,  # map missing for everyone
    )
    assert dropped == 0
    assert len(kept) == 2


def test_filter_skips_non_past_case_hits():
    """Guidelines / protocols never belong to a patient — never filter them."""
    bobby_hit = _h("L1-000100")
    guideline = Hit(
        source_id="GUIDE-CHEST-PAIN-ED",
        type="guideline",
        similarity=0.9,
        summary="chest pain ESI guideline",
        why_relevant="guideline match",
    )
    kept, dropped = filter_cross_patient(
        [bobby_hit, guideline],
        query_patient_id="PT-Bobby",
        hit_patient_of=lambda sid: "PT-Bobby" if sid == "L1-000100" else None,
    )
    kept_ids = {h.source_id for h in kept}
    assert dropped == 1
    assert kept_ids == {"GUIDE-CHEST-PAIN-ED"}


# ── apply_all_guards rollup ────────────────────────────────────────────────
def test_apply_all_guards_records_suppression_count():
    """End-to-end: leak filter fires, warning surfaces count."""
    out = RachelOutput(
        query_case_id="Bobby-visit-5",
        retrieved=[_h("L1-A"), _h("L1-B"), _h("L1-C")],
        retrieval_method="bm25",
    )
    owner = {"L1-A": "PT-Bobby", "L1-B": "PT-Alice", "L1-C": "PT-Bobby"}

    result = apply_all_guards(
        out,
        source_exists=lambda sid: True,  # all valid
        query_patient_id="PT-Bobby",
        hit_patient_of=lambda sid: owner.get(sid),
        min_score=0.0,
    )
    kept_ids = {h.source_id for h in result.retrieved}
    assert kept_ids == {"L1-B"}, f"expected only L1-B, got {kept_ids}"
    assert any(
        "suppressed 2 same-patient hits" in w for w in result.warnings
    ), f"expected suppression warning, got {result.warnings}"


def test_apply_all_guards_no_leaks_when_query_has_no_patient():
    """Without query patient_id, all valid hits pass through."""
    out = RachelOutput(
        query_case_id="anon-query",
        retrieved=[_h("L1-A"), _h("L1-B")],
        retrieval_method="bm25",
    )
    result = apply_all_guards(
        out,
        source_exists=lambda sid: True,
        query_patient_id=None,
        hit_patient_of=lambda sid: "PT-Bobby",
        min_score=0.0,
    )
    assert len(result.retrieved) == 2
    assert not any("same-patient" in w for w in result.warnings)


# ── baseline.retrieve degradation warning ──────────────────────────────────
def test_retrieve_warns_when_patient_id_given_but_identity_map_missing(monkeypatch):
    """If caller passes patient_id but the L1 identity map can't load,
    we must surface ONE warning so downstream knows the guard is no-op."""
    import shared.retrieval.baseline as baseline_mod

    monkeypatch.setattr(baseline_mod, "_identity_available", lambda: False)

    out = baseline_mod.retrieve(
        "62yo male hypertension",
        query_case_id="Q-NO-MAP",
        k=3,
        patient_id="PT-Bobby",
        method="bm25",
    )
    assert any(
        "patient identity map unavailable" in w for w in out.warnings
    ), f"expected degradation warning, got {out.warnings}"


def test_retrieve_no_warning_when_no_patient_id_even_if_map_missing(monkeypatch):
    """No patient_id = no enforcement asked for = no warning needed."""
    import shared.retrieval.baseline as baseline_mod

    monkeypatch.setattr(baseline_mod, "_identity_available", lambda: False)

    out = baseline_mod.retrieve(
        "62yo male hypertension",
        query_case_id="Q-NO-PID",
        k=3,
        patient_id=None,
        method="bm25",
    )
    assert not any("patient identity map" in w for w in out.warnings)
