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

## 8. 🚨 AI Crime Report

> **Every failure mode this system catches, named, with detection + audit + action.** When an interviewer asks *"what about X?"* the answer points at one row of this table. No vibes.

```
─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #1 — AI LIES (HALLUCINATION)
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     services/guardrails-api → output_guardrails.hallucination_check
                 + offline Ragas faithfulness re-eval (weekly)
Audit captures:  hallucination_score, claim text, retrieved sources, trace_id
Auto-action:     block output → refusal template; log + flag for golden-set review
Baseline:        Ragas faithfulness 0.958 (n=50). Threshold to ship: ≥ 0.85.
                 Drop below → page on-call.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #2 — AI LEAKS PHI
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     input_guardrails.redact_pii (spaCy NER + regex, 18 HIPAA identifiers)
                 + Llama Guard S7 (privacy) classification on output
                 + offline log scan for SSN/MRN-shaped strings
Audit captures:  pii_redactions count, redaction_method, leaked_token_pattern (if any)
Auto-action:     fail-closed if redaction returns 0 hits on PHI-shaped input;
                 page privacy officer; block all triages until patch deployed
Baseline:        1,753 PII tokens redacted on 200-Q&A test. PHI-redaction
                 success rate gate: ≥ 99.5%.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #3 — AI TIMES OUT
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     LLM SDK timeout (20s default, configurable per pattern)
Audit captures:  attempt_count, total_duration_ms, final_state="timeout_refusal"
Auto-action:     exponential backoff (1s · 2s · 4s · max 3 retries) →
                 if all fail: refusal template, NOT crash;
                 banner: "AI unavailable, use manual triage"
Threshold:       LLM error rate > 2% rolling 5-min → page on-call

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #4 — AI GETS JAILBROKEN
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     input_guardrails.strip_prompt_injection (regex + classifier)
                 + Llama Guard secondary safety
                 + weekly red-team regression test (50 prompts, 5 categories)
Audit captures:  injection_pattern_matched, attack_category (PII/inject/jailbreak/
                 leak/hijack), classifier_verdict
Auto-action:     strip + log; if Llama Guard flags "unsafe" → escalate to safety officer;
                 if regression test < 100% block → IMMEDIATE page + PR blocker
Baseline:        100% block rate on 50 adversarial prompts. Any regression =
                 production hold.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #5 — CLOUD DIES (PROVIDER OUTAGE)
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     5xx rate per cloud provider, rolling 5-min window
Audit captures:  provider, error_code, total_5xx_in_window, fallback_used
Auto-action:     after 30s sustained 5xx → operator paged; manual env-var swap
                 to backup CloudProvider (NOT auto-failover — auto introduces
                 consistency bugs); banner: "AI degraded, using backup cloud"
Why not auto:    automatic cross-cloud failover at this scale is overkill +
                 risks split-brain. Manual swap is the right call.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #6 — RETRIEVAL DIES (EMBEDDING/VECTOR-STORE FAIL)
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     vector_search timeout (2s) or embedding API 5xx
Audit captures:  retrieval_method=("embedding" | "bm25_fallback"), latency_ms
Auto-action:     graceful degradation to BM25 lexical search (already wired);
                 caller still gets results, just lower quality
                 Mark trace: retrieval_method="bm25_fallback"
Why fallback:    BM25 over the 55K-row corpus catches ~13% (verified via
                 context_recall in baseline) — degraded but not silent fail

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #7 — EVAL SILENTLY SKIPS
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     CI step exit code on Ragas eval-on-PR run
Audit captures:  ci_run_id, eval_status=("ran"|"skipped"|"failed"), reason
Auto-action:     if eval can't run (judge LLM unavailable, dataset missing) →
                 CI marks PR "eval skipped — manual review required";
                 does NOT auto-pass; merge blocked until human reviews
Why this matters: silent eval skip = silent regression. The system fails
                  loud, never silent.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #8 — AI CONFIDENCE FAKE-HIGH (MISCALIBRATION)
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     output_guardrails.confidence_check
                 (|stated_confidence - evidence_strength| > threshold)
                 + offline Expected Calibration Error (ECE) on classifier eval
Audit captures:  stated_confidence, evidence_strength, miscalibration_delta
Auto-action:     when stated > evidence by > 0.2 → flag in trace, demote
                 confidence band shown to nurse; classifier ECE > 0.1
                 → re-train signal
Why this matters: a confident-wrong answer in clinical settings is worse
                  than an uncertain-right one. Honesty about uncertainty
                  is itself a safety property.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #9 — NURSE OVERRIDES AI
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     UI logs every override action with reason
Audit captures:  human_override_bool=true, override_reason_text, ai_suggestion,
                 nurse_id, esi_tier_predicted, esi_tier_actual
Auto-action:     no block — clinical authority always wins. But:
                 KPI tracked = override rate per ESI tier
                 > 30% override rate on a tier → retrain signal for that tier
Why this matters: override rate is the gold-standard quality signal.
                  Nurse overrides are NOT a failure — they're the system
                  working as designed (HITL). Silent agreement at 100% is
                  more suspicious than 5-10% override.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #10 — DRIFT SLOWLY POISONS MODEL
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     shared/anomaly/drift.py centroid-shift on weekly batches
                 + Layer 3 weekly Ragas re-run vs baseline
Audit captures:  drift_score, σ_threshold_breached_bool, baseline_delta
Auto-action:     centroid-shift > 1σ → page on-call;
                 banner deployed on every triage UI: "drift active —
                 manual review recommended" until cleared;
                 root-cause owned by Layer 1 (usually = source data shifted,
                 e.g. new EHR template — Layer 1 dbt test should catch upstream)
Why "regulator-loved": every health-system AI procurement RFP asks
                       "how do you detect drift?" If you don't have
                       this answer, you can't sell.

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #11 — COST EXPLODES
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     rolling 1h cost tracker per app + per cloud provider
Audit captures:  cost_usd per call, model_tier_used, total_burn_rate_usd_per_hour
Auto-action:     burn rate > 2× baseline → warn (Slack);
                 burn rate > 5× baseline → automatic tier-router downgrade
                 (force-route everything to Haiku/Flash for next 1h);
                 page FinOps if sustained > 30min
Baseline:        Cost router achieves 62.2% reduction vs GPT-4o baseline.
                 Watch for tier-distribution shift (Sonnet usage > 30% =
                 something's wrong upstream).

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #12 — LATENCY SPIKES
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     P95 latency per pattern, rolling 1-min window
                 (cloud-native APM: Cloud Logging / App Insights / CloudWatch)
Audit captures:  latency_ms per call, pattern, model_tier, cache_hit_bool
Auto-action:     P95 retrieval > 500ms → warn;
                 P95 > 2s → page;
                 P95 > 5s sustained → fallback ladder kicks in
                 (BM25-only retrieval, refusal templates for generation)
Common causes:   embedding service degraded · cache miss rate spike ·
                 cloud region issue (see Crime #5)

─────────────────────────────────────────────────────────────────────────────────────────
🚨 CRIME #13 — HALLUCINATION RATE RISES
─────────────────────────────────────────────────────────────────────────────────────────
Detected by:     daily Ragas faithfulness re-run (Crime #1 baseline)
                 + per-call hallucination_check (Crime #1 runtime)
                 + offline correlation: traces with override_reason_text
                 mentioning "wrong" / "made up" / "not in record"
Audit captures:  daily_avg_faithfulness, traces_with_hallucination_keyword
Auto-action:     daily faithfulness < 0.85 → page on-call + freeze model
                 version on production app;
                 root cause loop: 1) check Crime #6 (retrieval degraded?)
                 2) check Crime #10 (drift?) 3) check Crime #4 (jailbreak
                 in production traffic?)
Why daily:       slow drift in hallucination is the nastiest failure
                 mode — it doesn't trip per-call alerts but degrades
                 trust over weeks. Daily re-run catches it.
─────────────────────────────────────────────────────────────────────────────────────────
```

## How the crime report fits the pillars

```
🎯 ACCURACY     covers crimes #1, #8, #13
⚡ SPEED         covers crimes #3, #12
💰 COST          covers crime #11
🛡️ COMPLIANCE   covers crimes #2, #4, #7, #9, #10
🤖 INNOVATION   covers crimes #5, #6 (graceful degradation IS architecture)
🌟 OUTCOME       crime #9 (override rate) is itself a quality KPI
```

Every crime maps to at least one pillar. Every pillar has at least one named crime backing it. **No safety claim without a named detection mechanism.**

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
