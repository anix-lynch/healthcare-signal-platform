# 02 — Operational Realism

> **What this doc is for.** Demo projects fall apart the moment an interviewer asks *"what happens when the LLM times out?"* This doc lists the production behaviors this system handles (or has explicit plans to handle), so the answer is concrete instead of "I'd add that."

> **What this doc is NOT.** A K8s manifest, a service mesh, an event bus, or any other infra cosplay. Real enterprise AI systems are surprisingly boring at the infra level. Most of the value is in **explicit failure handling and audit discipline**, not in operator sophistication.

---

## 1. Retry handling

```
WHERE                            BEHAVIOR
─────────────────────────────────────────────────────────────────────────────────────────
LLM API call (any pattern)        Exponential backoff: 1s · 2s · 4s · max 3 retries.
                                  After 3 failures: degrade to refusal response, not crash.
                                  Reason: transient 5xx from cloud LLM ~1-2% in normal ops.

Embedding call                    Same backoff. On final fail, fall back to BM25-only retrieval
                                  (graceful degradation — caller still gets results, just lower
                                  quality).

Cloud provider failover           If CLOUD_PROVIDER=vertex returns 5xx for 30+ seconds,
                                  factory.py exposes a manual switch to azure or aws.
                                  Not auto-failover (auto across clouds is overkill for this
                                  scale + introduces consistency bugs).

Eval-on-PR                        If Ragas eval fails to run (judge LLM unavailable),
                                  CI marks PR as "eval skipped — manual review required."
                                  Does NOT auto-pass. Reason: silent eval skip = silent regression.
```

## 2. Timeout handling

```
COMPONENT                         TIMEOUT      ON TIMEOUT
─────────────────────────────────────────────────────────────────────────────────────────
LLM completion                    20s          Refuse with structured error, log trace ID.
Vector search                     2s           Fall back to BM25.
Cloud feature-api lookup          500ms        Fall back to last-known-good cached feature.
Audit log write                   200ms (async) Drop to local disk queue, retry from queue
                                                 (NEVER block clinical decision on audit).
Llama Guard secondary safety      5s           Fail-closed — if can't classify, refuse output.
Ragas eval (per query)            30s          Skip query, log + continue (eval is best-effort).
```

## 3. Fallback paths

```
PATTERN                           PRIMARY                       FALLBACK
─────────────────────────────────────────────────────────────────────────────────────────
Retrieval (Rachel)                embedding + vector search     BM25 lexical (already implemented)
Generation (Mad Lib)              LLM with structured output    refusal template ("I cannot
                                                                 generate a recommendation
                                                                 without retrieval context")
Classification (Traffic Light)    LLM with structured output    rule-based ESI classifier
                                                                 (chief-complaint keyword match —
                                                                 less accurate but always works)
LoS regression (Crystal Ball)     LightGBM on embedding features simple median-by-cohort lookup
PII redaction                     spaCy NER + regex             regex-only (NER fail = degrade,
                                                                 not bypass)
```

**Fallback principle:** every clinical-path component must have a non-LLM degraded mode. AI is augmentation, not single-point-of-failure.

## 4. Versioned APIs

```
SERVICE                  VERSIONING SCHEME           BREAKING CHANGE POLICY
─────────────────────────────────────────────────────────────────────────────────────────
services/rag-api         /v1/search · /v1/generate   New version = new path. v1 + v2 run in
                                                      parallel for 90 days minimum during transition.
services/guardrails-api  /v1/sanitize · /v1/validate  Same.
services/feature-api     /v1/features/{id}            Same. Schema changes = bump.
services/analytics-api   /v1/metrics/{name}           Same.

Layer 1 OpenAPI contract  semver in openapi.json     Major bump on field-rename or
                                                      type-change. Minor bump on
                                                      additive only.
```

## 5. Audit logging

Every LLM call writes a trace record to the active CloudProvider's audit sink:

```
TRACE RECORD (JSON, structured):
{
  "trace_id":          "uuid",
  "session_id":        "uuid (links to one ER visit)",
  "patient_id_hash":   "sha256 of patient_id (never raw PHI in logs)",
  "pattern":           "rachel | traffic_light | mad_lib | ...",
  "model":             "claude-haiku-4-5 | gemini-2.5-flash | ...",
  "cloud":             "vertex | azure | aws",
  "prompt_tokens":     int,
  "completion_tokens": int,
  "cost_usd":          float,
  "latency_ms":        int,
  "input_guardrails":  {pii_redactions: int, injection_blocked: bool},
  "output_guardrails": {hallucination_score: float, citations: [...]},
  "fallback_used":     bool,
  "decision":          "NOW | SOON | WAIT | REFUSED",
  "human_overrode":    bool
}

DESTINATION (per CloudProvider):
- Vertex   → Cloud Logging
- Azure    → Application Insights
- AWS      → CloudWatch Logs

RETENTION: 7 years (HIPAA requirement, configurable per cloud).
```

## 6. Escalation rules

When the system MUST hand off to a human, even if the LLM has high confidence:

```
TRIGGER                                   ACTION
─────────────────────────────────────────────────────────────────────────────────────────
ESI tier 1 case                            → Page on-call attending immediately. AI logs
                                             but does NOT auto-decide.
Pediatric < 1 year old                     → Always human-reviewed before AI suggestion shown.
Suicidal ideation in chief complaint       → Behavioral health protocol. AI only documents.
Confidence < 0.6 on triage tier            → Show AI suggestion + "AI uncertain" banner.
                                             Nurse confirms before action.
Drift alert active in last 24h             → Show "drift active — manual review" banner
                                             on every triage until cleared.
PII redaction failed                        → Block output. Do NOT show partial redaction.
Llama Guard returns "unsafe"               → Refuse + escalate to safety officer.
Output guardrail rejection                 → Refuse with reason logged. Nurse re-prompts manually.
```

Hard rules live in `apps/er-triage/safety/safety_agent.py`.

## 7. Observability notes

```
SIGNAL                            COLLECTED                    ALERT THRESHOLD
─────────────────────────────────────────────────────────────────────────────────────────
LLM error rate                    rolling 5-min window         > 2% → Slack page on-call
P95 retrieval latency             rolling 1-min                > 500ms → warn, > 2s → page
Cost burn rate                    rolling 1h                   > 2× baseline → warn
Eval baseline drift               daily Ragas re-run            faithfulness < 0.85 → page
Red-team block rate               weekly re-run                 < 100% → IMMEDIATE page
PHI redaction success rate        per-call                      < 99.5% → page privacy officer
Cloud provider availability       per-request                  > 5% 5xx for 5min → manual swap
```

These are tracked even though the underlying observability stack is "whatever your cloud provides" — Cloud Logging, App Insights, or CloudWatch. **Don't build a custom observability stack for a system this size.** Use what the cloud gives you and document the queries.

---

## What this section deliberately does NOT include

```
❌ Kubernetes manifests        — overkill for a system this size, infra cosplay
❌ Service mesh (Istio/Linkerd) — same
❌ Event bus (Kafka/Pulsar)    — synchronous HTTP is fine for this scale
❌ Custom observability stack  — use cloud-native, document the queries
❌ Multi-region failover       — single-region is the right starting point
❌ Microservices proliferation — 4 services covers the actual surface area
```

The principle: **production-realistic ≠ FAANG-scale.** A 50-bed hospital doesn't need K8s. It needs explicit failure handling and audit discipline. This doc shows we have those.

---

## Cross-references

- **Per-pattern eval methodology:** [`../layer2-ai-application/apps/er-triage/docs/05_seven_lens_dashboard.md`](../layer2-ai-application/apps/er-triage/docs/05_seven_lens_dashboard.md)
- **Patient lifecycle flow (where these behaviors fire):** [`../flows/patient_lifecycle.md`](../flows/patient_lifecycle.md)
- **Architecture diagrams:** [`../diagrams/`](../diagrams/)
