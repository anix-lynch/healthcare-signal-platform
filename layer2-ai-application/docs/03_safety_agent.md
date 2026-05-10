# Safety Agent — Hard-Rule Overlay

> **Architecture source:** [`mj/docs/tool_calling.md`](file:///Users/anixlynch/dev/mj/docs/tool_calling.md) — Level-2 Agent.

## Why hard rules

LLMs are soft classifiers. They're 90-95% right. The remaining 5-10% includes life-threatening errors. **Hard rules are non-negotiable overrides on top of LLM verdicts.**

## Hard rule taxonomy (initial)

```yaml
# configs/safety_rules.yaml (to write)

never_below_tier_2:
  - chest_pain:
      triggers: ["chest pain", "chest pressure", "substernal", "angina"]
      severity_keywords: ["radiating", "diaphoretic", "shortness of breath"]
  - stroke_signs:
      triggers: ["facial droop", "slurred speech", "FAST positive",
                 "weakness one side", "sudden confusion"]
  - altered_mental_status:
      triggers: ["AMS", "altered", "confused", "unresponsive",
                 "GCS < 15"]
  - anaphylaxis:
      triggers: ["anaphylaxis", "throat swelling", "stridor",
                 "diffuse hives + dyspnea"]
  - active_major_bleeding:
      triggers: ["GSW", "stab wound", "hemorrhaging",
                 "uncontrolled bleeding"]
```

## Algorithm

```
def review(case, llm_verdict):
    for rule in load_rules():
        if rule.matches(case):
            if llm_verdict.esi_tier > rule.max_tier:
                # OVERRIDE
                return ESIVerdict(
                    esi_tier=rule.max_tier,
                    confidence=1.0,
                    reasoning=f"Safety override: {rule.name}",
                    red_flags=[rule.name],
                    overridden_from=llm_verdict.esi_tier,
                )
    return llm_verdict
```

## Override is one-way

Safety Agent can only **lower** the tier number (more urgent), never raise it. This prevents the LLM from being too cautious AND prevents Safety Agent from being too lenient.

## Audit trail

Every override is logged:
```
{
  "case_id": "...",
  "llm_tier": 4,
  "overridden_to": 2,
  "rule_triggered": "chest_pain",
  "match_text": "substernal pressure 30 min",
  "timestamp": "...",
}
```

This log is what regulators ask for.

## Tests

`tests/test_safety_overrides.py` verifies each rule:
- Synthesize a case that triggers the rule
- Mock LLM verdict at tier 3-5
- Assert Safety Agent overrides to tier ≤ 2
- Assert audit trail contains the rule name
