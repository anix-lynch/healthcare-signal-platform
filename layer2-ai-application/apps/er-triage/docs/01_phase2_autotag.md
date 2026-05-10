# Phase 2 — ESI Auto-Tagger

> **Concept source:** [`mj/docs/02_traffic_light.md`](file:///Users/anixlynch/dev/mj/docs/02_traffic_light.md) and [`mj/docs/autotagging_llm_as_classifier_intake_automation.md`](file:///Users/anixlynch/dev/mj/docs/autotagging_llm_as_classifier_intake_automation.md)

## Recipe (drillable)

1. **Define taxonomy** — ESI 1-5 (already done, official rubric)
2. **Write prompt** — see `app/classify/prompts.py`
3. **Pick model** — Haiku default (~$0.001/case), Sonnet fallback for low-confidence
4. **Hand-label 30 golden cases** — `inputs/golden_esi.json` (10× ESI-1, 10× ESI-2, 5× ESI-3, 3× ESI-4, 2× ESI-5)
5. **Implement classify()** — Pydantic structured output
6. **Run smoke test** — `make smoke`
7. **Iterate prompt** with few-shot examples for confused tier pairs
8. **Wire Safety Agent** as the post-classify reviewer
9. **Ship to ER2/app/engine.py** — call `classify()` then `SafetyAgent.review()`

## Output schema (Pydantic)

```python
class ESIVerdict(BaseModel):
    esi_tier: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=20)  # regulator audit trail
    red_flags: list[str] = []
    resources_expected: int = Field(ge=0)
```

## Cost expectation

- Haiku: ~$0.001/case
- 200 cases/day average → $6/month
- 1000 cases/day at scale → $30/month
- Sonnet upgrade for ambiguous cases → ~10% of traffic, +$3/month

## Failure modes to test

| Scenario | Expected behavior |
|---|---|
| Vague chief complaint | confidence < 0.5, route to human |
| Conflicting vitals (BP normal but HR 180) | flag in red_flags |
| Pediatric case (different rubric) | confidence < 0.7, escalate |
| Non-English HPI | confidence drops, route to human |
