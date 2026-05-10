# 05 — Seven-Lens × 6-Pillar × Multi-Cloud Dashboard

> **What this is.** The reference matrix that wires every ER3 module to the eval metric it produces, the Nora Bing pillar that metric serves, and which cloud provider runs it. Print this. Pin it next to the IDE.

---

## The full matrix

```
PATTERN          MODULE                      EVAL METRIC                    PILLAR(S)        CLOUD COVERAGE
─────────────────────────────────────────────────────────────────────────────────────────────────────────────
Rachel           app/retrieval/              P@K · NDCG · Recall@K          🎯 ACCURACY      Vertex · Azure · AWS
                 retriever.py                                                ⚡ SPEED (cache)

Traffic Light    app/classify/               accuracy · F1 · calibration    🎯 ACCURACY      Vertex · Azure · AWS
                 esi_classifier.py                                           🛡️ COMPLIANCE
                                                                             💰 COST (gating)

Crystal Ball     app/regress/                MAE · R² · structured-validity 🛡️ COMPLIANCE   Vertex · Azure · AWS
                 los_predictor.py                                            🎯 ACCURACY

Mad Lib          app/generate/               faithfulness · groundedness ·  🎯 ACCURACY      Vertex · Azure · AWS
                 chart_note.py               LLM-judge                       🛡️ COMPLIANCE

Smoke Detector   app/anomaly/                precision/recall ·             🛡️ COMPLIANCE   Vertex · Azure · AWS
                 drift.py + flagger.py       centroid-shift score            🎯 ACCURACY

Treasure Map     app/cluster/                silhouette ·                   🌟 OUTCOME       Vertex · Azure · AWS
                 cohort.py                   BERTopic coherence              🎯 ACCURACY

Police Lineup    app/rank/                   NDCG · MRR ·                   ⚡ SPEED         Vertex · Azure · AWS
                 reranker.py                 win-rate vs baseline            🎯 ACCURACY
```

## Cross-cutting modules (not patterns, but pillar contributors)

```
MODULE                          ROLE                            PILLAR(S)
──────────────────────────────────────────────────────────────────────────────
app/safety/safety_agent.py      hard-rule medical overrides     🛡️ COMPLIANCE
app/guardrails/input_*           prompt sanitize + PII redact    🛡️ COMPLIANCE
app/guardrails/output_*          hallucination + citation gate   🛡️ COMPLIANCE + 🎯
app/memory/memory.py             3-tier triage memory            🤖 INNOVATION
app/cloud/                       multi-cloud adapter             🤖 INNOVATION + 🛡️
```

## The 6-pillar resume map

When a recruiter says "tell me about your AI rigor," walk down the pillars:

```
🎯 ACCURACY     "I run faithfulness + LLM-judge on every PR via the
                 generate_eval module. P@K and NDCG measured per-pattern.
                 Calibration error tracked on the classifier."

⚡ SPEED         "Police Lineup funnels: cheap BM25 → cross-encoder → judge.
                 Rachel uses cached embeddings. P95 retrieval < 300ms."

💰 COST         "Traffic Light tier-routes: cheap classify gates expensive
                 Mad Lib. Only ESI 2-3 trigger the full RAG path."

🛡️ COMPLIANCE   "Two-layer guardrails: input (PII redact, prompt-injection
                 strip) and output (citation validation, hallucination
                 check). Plus a domain Safety Agent for medical hard rules.
                 Drift monitor on every weekly batch."

🤖 INNOVATION   "Agent-friendly architecture: MCP tool contracts, OpenAPI
                 per service, JSON-stdout CLIs, env-var cloud switch via
                 CloudProvider adapter — Vertex / Azure / AWS interchangeable."

🌟 OUTCOME      "ER3 turns ER2's 2-pattern MVP into a 7-pattern system
                 with universal eval harness. % patterns auto-evaluated
                 on every PR: 7/7. # clouds supported: 3."
```

## The 7-pattern interview drill

Memorize the metric for each pattern. When tech screen asks "how do you eval X?" — answer in <5 seconds:

```
"Retrieval? — P@K, NDCG, Recall@K. We use a 30-case golden set."
"Classification? — accuracy, macro-F1, calibration error."
"Regression? — MAE, R², plus structured-output validity rate."
"Generation? — faithfulness, groundedness, LLM-judge with calibration."
"Anomaly? — precision/recall on synthetic outliers, centroid-shift drift."
"Clustering? — silhouette score, BERTopic coherence on auto-labels."
"Ranking? — NDCG, MRR, win-rate vs single-stage BM25 baseline."
```

That's 7 sentences. Drill them until automatic.

---

## Cross-references

- **6-pillar canon:** [`mj/docs/nora_bing_metric.md`](file:///Users/anixlynch/dev/mj/docs/nora_bing_metric.md)
- **Role-KPI reverse map:** [`fail-fwd/possibletitle/genai_role_kpi_trees.md`](file:///Users/anixlynch/dev/FWD/fail-fwd/possibletitle/genai_role_kpi_trees.md)
- **Cookie-cutter framework:** [`fail-fwd/cookiecutter_by_role.md`](file:///Users/anixlynch/dev/FWD/fail-fwd/cookiecutter_by_role.md)
