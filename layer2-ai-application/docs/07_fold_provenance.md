# 07 — Fold Provenance: healthcare-rag-guardrails → ER3

> **Date:** 2026-05-09
> **Source repo:** [`anix-lynch/healthcare-rag-guardrails`](https://github.com/anix-lynch/healthcare-rag-guardrails)
> **Decision:** Hard fold. The source repo had real, JSON-backed implementations
> that closed gaps in ER3's stub modules. Rather than maintain two repos with
> overlapping concerns, all substantive code + data was migrated into ER3.

---

## Why fold (vs. keep separate)

ChatGPT recommended keeping the repos separate ("more repos = more angles").
That logic is wrong for Bchan's situation:

1. **ER3 had stub guardrails.** Every method raised `NotImplementedError`.
   `healthcare-rag-guardrails` had real Ragas eval, real PII masking with
   1,753 redactions verified, and a real 50-prompt red-team suite at 100%
   block rate. Folding turned ER3 from skeleton-grade to braggable-grade.

2. **One flagship beats two thin repos** for the target roles
   (Architect / FDE / Consultant / Platform). Recruiters want to see safety
   *baked into* the showcase product, not as a separate "I can also do this"
   side project.

3. **"Less is more"** — Bchan's stated rule. Trim demo-grade noise from the
   showroom; concentrate signal in the flagship.

---

## What got folded (file-by-file)

```
SOURCE                                          DESTINATION                                     STATUS
─────────────────────────────────────────────────────────────────────────────────────────────────────────
scripts/01_gen_healthcare_qa.py            →   ER3/scripts/gen_healthcare_qa.py            verbatim copy
scripts/02_run_ragas_healthcare.py         →   ER3/scripts/run_ragas_eval.py               verbatim copy
scripts/03_classifier_router.py            →   ER3/app/classify/router.py                  verbatim copy
scripts/04_pii_masker.py                   →   ER3/scripts/run_pii_masker.py               verbatim copy
                                                + impl folded into
                                                ER3/app/guardrails/input_guardrails.py
                                                (replaces redact_pii() stub)
scripts/05_llama_guard.py                  →   ER3/app/guardrails/llama_guard.py           verbatim copy
scripts/06_redteam_suite.py                →   ER3/scripts/run_redteam_suite.py            verbatim copy
                                                + ER3/tests/red_team/                      pytest wrapper

data/healthcare_qa_200.json                →   ER3/inputs/healthcare_qa_200.json           verbatim
data/ragas_healthcare_results.json         →   ER3/outputs/baseline/ragas_baseline.json    verbatim
data/redteam_block_rate.json               →   ER3/outputs/baseline/redteam_baseline.json  verbatim
data/router_results.json                   →   ER3/outputs/baseline/router_baseline.json   verbatim
```

## Real numbers inherited (replace the README placeholders)

```
PILLAR        METRIC                                 VALUE        SOURCE FILE
─────────────────────────────────────────────────────────────────────────────────────────────────────────
🎯 ACCURACY   Ragas faithfulness                     0.9578       outputs/baseline/ragas_baseline.json
              Ragas answer_relevancy                 0.8561       outputs/baseline/ragas_baseline.json
              Ragas context_recall                   0.1275 ⚠️    outputs/baseline/ragas_baseline.json
              n samples                              50

💰 COST       Cost reduction (vs GPT-4o baseline)    62.2%        outputs/baseline/router_baseline.json
              n queries                              100
              Tier distribution                      32/52/16     (Haiku/Flash/Sonnet)

🛡️ COMPLIANCE PII tokens redacted                    1,753        (regex + spaCy NER baseline)
              Red-team block rate                    100%         outputs/baseline/redteam_baseline.json
              Attack categories tested               5            (PII / inject / jailbreak / leak / hijack)
              n adversarial prompts                  50           (10 per category)
```

### ⚠️ Honest gap: context_recall = 0.1275

BM25 over a 55K-row CSV with Q&A-style queries finds the right context
~13% of the time. That's a known limitation of lexical retrieval on
paraphrased questions. The fix is the Pattern 1 (Rachel) embedding-based
retrieval which lives in `app/retrieval/`. The tracked work to close this:

1. Re-run the Ragas eval with embedding retrieval (Vertex Vector Search
   or Chroma) instead of BM25.
2. Expected lift: context_recall → 0.6-0.8 with `text-embedding-005` +
   sentence-transformers cross-encoder rerank.

**This is honest. In an interview, "we identified BM25 was weak and the
fix is queued" beats "we report 0.96 and don't mention recall."** Don't
hide context_recall — own it.

---

## Source repo disposition

```
healthcare-rag-guardrails (GitHub)
   ├── DON'T DELETE — preserves git history + prior URLs
   ├── README.md TOP: Add notice
   │   "📦 This work has been integrated into ER3 (https://github.com/anix-lynch/er-triage-v3)
   │    as the eval + guardrails layer. This repo is preserved for history."
   └── Archive on GitHub (Settings → Danger Zone → Archive)
       (read-only, hidden from search, signal of supersession)
```

---

## Phase-5 follow-ups (not blocking — but tracked)

```
☐ Wire ragas eval through CloudProvider abstraction (currently OpenAI direct)
☐ Replace BM25 with embedding retrieval to close context_recall gap
☐ Re-baseline all 4 JSONs after CloudProvider wiring
☐ Add eval-on-PR via GitHub Actions (regression gate)
☐ Add MLflow tracking for run-to-run history
```

---

## Cross-references

- **Source repo (archived):** github.com/anix-lynch/healthcare-rag-guardrails
- **6-pillar dashboard:** [`README.md`](file:///Users/anixlynch/dev/ER3/README.md)
- **Seven-lens dashboard:** [`docs/05_seven_lens_dashboard.md`](file:///Users/anixlynch/dev/ER3/docs/05_seven_lens_dashboard.md)
- **Foldability decision matrix:** session log 2026-05-09 chat
