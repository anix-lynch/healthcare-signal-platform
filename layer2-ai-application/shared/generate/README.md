# Pattern 4 — Mad Lib 📖

> **"explain this shit to humans 😭"**

Generation. Grounded in Rachel hits + Traffic Light tier. Every claim cites
a Rachel `source_id`. Without grounding, every chart note hallucinates.

## File map

```
shared/generate/
├── __init__.py        public API (generate_note, MadLibOutput)
├── schema.py          Pydantic output contract
├── baseline.py        wraps chart_note.generate(); validates citations
├── chart_note.py      template-based engine (existing, working)
└── README.md          you are here
```

## What's shipped

```
template-based chart note     ✅ shipped
nurse handoff (SBAR-shaped)   ✅ shipped
patient explanation           ✅ shipped
citation validation           ✅ shipped (drops unresolved IDs, warns)
faithfulness_score (Ragas)    ⚠️ offline only — eval harness in layer3
LLM enhance path              ⚠️ stub in engine (enhance=True flag)
```

## Mad Lib's brutal mantra

```
template alone     = boring but never hallucinates
LLM alone          = beautiful prose that cites cases that don't exist
template + cite    = boring + safe + auditable
template + cite + LLM polish = production
```

## Together with the other patterns

```
Rachel surfaces hits           →  Mad Lib grounds in them
Traffic Light decides tier     →  Mad Lib uses tier for disposition
Crystal Ball numbers           →  Mad Lib slots LoS + readmission risk

if you skip the citation gate, the lawyer notices first 💀
```

## Quick start

```python
from shared.retrieval import retrieve_for_case
from shared.classify import triage
from shared.generate import generate_note

case = {"cc": "chest pain", "hpi": "62yo M, substernal pressure, diaphoresis"}
tl = triage(case, case_id="CASE-104").model_dump()
rachel = retrieve_for_case(case, query_case_id="CASE-104", k=5).model_dump()["retrieved"]

out = generate_note(case, tl, case_id="CASE-104", rachel_hits=rachel)
print(out.model_dump_json(indent=2))
```
