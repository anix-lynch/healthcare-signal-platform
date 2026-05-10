# Demos · Screenshots · API Examples

> **What goes here:** evidence a recruiter can SEE without setting up the system. Screenshots, traces, JSON examples, walk-throughs. **Currently scaffolded — content lands here as it's produced.**

---

## Planned contents (Phase 5)

```
demos/
├── README.md                                 (you are here)
├── api_examples.md                           curl examples + JSON I/O for
│                                              each service (rag-api,
│                                              guardrails-api, feature-api,
│                                              analytics-api)
├── trace_examples.md                         what a real trace record looks
│                                              like (synthetic until first
│                                              live deploy)
├── eval_walkthrough.md                       reading the Ragas + redteam +
│                                              router baseline JSONs (already
│                                              in apps/er-triage/outputs/baseline/)
├── screenshots/
│   ├── trace_view.png                        Cloud Logging filtered to one
│   │                                          patient session (PHI redacted)
│   ├── retry_fallback.png                    when LLM 5xx, system falls
│   │                                          back to BM25 — captured in trace
│   ├── eval_dashboard.png                    Ragas trend over time
│   ├── redteam_baseline.png                  100% block-rate verification
│   ├── audit_log_entry.png                   one full structured audit record
│   ├── powerbi_executive.png                 executive dashboard view
│   └── ops_routing_decision.png              ops-capacity-assistant output
└── walkthroughs/
    ├── 01_patient_arrival_to_decision.md     end-to-end with screenshots
    ├── 02_drift_detection_response.md        what happens when drift fires
    └── 03_red_team_regression_block.md       PR blocked because redteam < 100%
```

---

## What's available NOW (without screenshots)

```
EVIDENCE                                      LIVES AT                                   FORMAT
────────────────────────────────────────────────────────────────────────────────────────────────────
Ragas eval baseline                           apps/er-triage/outputs/baseline/           JSON
                                              ragas_baseline.json                        (50 samples)
Red-team block rate                           apps/er-triage/outputs/baseline/           JSON
                                              redteam_baseline.json                      (50 prompts,
                                                                                          5 categories)
3-tier router cost analysis                   apps/er-triage/outputs/baseline/           JSON
                                              router_baseline.json                       (100 queries)
Healthcare Q&A eval corpus                    apps/er-triage/inputs/                     JSON
                                              healthcare_qa_200.json                     (200 pairs)
Golden ESI smoke set                          apps/er-triage/inputs/                     JSON
                                              golden_esi.json                            (30 cases)
Pattern eval methodology                      apps/er-triage/docs/                       Markdown
                                              05_seven_lens_dashboard.md
```

---

## How a recruiter reads this WITHOUT a demo

If they want to verify "this is real and not vibes," point them at:

```
EVIDENCE TRAIL                                                READS LIKE
───────────────────────────────────────────────────────────────────────────────────────
1. apps/er-triage/outputs/baseline/ragas_baseline.json        "0.958 faithfulness, 50
                                                               samples, Claude Haiku judge,
                                                               BM25 retrieval over 55K-row
                                                               healthcare CSV"

2. apps/er-triage/outputs/baseline/redteam_baseline.json      "100% block across 5
                                                               attack categories, 50
                                                               prompts, all blocked"

3. layer3-governance/scripts/06_redteam_suite.py              "the actual 50 adversarial
                                                               prompts you can read +
                                                               re-run"

4. layer3-governance/data/healthcare_qa_200.json              "200 generated Q&A pairs
                                                               from the 55K-patient
                                                               synthetic corpus"
```

Numbers + scripts + corpus + adversarial prompts — every claim in the README has a file behind it. That's the answer to "is this real?"

---

## What makes a good demo screenshot (for when we add them)

```
✅ Show the system DOING something, not just an empty UI
✅ Include trace IDs / timestamps so a viewer can verify reproducibility
✅ Show one good case AND one failure case (retry, fallback, refusal)
✅ PHI must be redacted in any captured trace — use synthetic patient_id_hash
✅ Caption every screenshot with WHAT pillar/pattern it demonstrates
   (🎯 ACCURACY, 💰 COST, 🛡️ COMPLIANCE, 🤖 INNOVATION, 🌟 OUTCOME)

❌ Don't show pure-marketing screens (pretty splash pages, hero text)
❌ Don't show framework dashboards (LangSmith branded, etc.) — show YOUR
   trace structure
❌ Don't show happy-path-only — interviewers care about failure modes
```

---

## Cross-references

- **Eval methodology behind the JSON baselines:** [`../layer2-ai-application/apps/er-triage/docs/05_seven_lens_dashboard.md`](../layer2-ai-application/apps/er-triage/docs/05_seven_lens_dashboard.md)
- **Patient flow that demos illustrate:** [`../docs/05_patient_lifecycle.md`](../docs/05_patient_lifecycle.md)
- **Operational behaviors demos should show:** [`../docs/02_operational_realism.md`](../docs/02_operational_realism.md)
