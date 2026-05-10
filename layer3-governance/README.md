# Healthcare RAG Guardrails — Eval & Compliance Suite

A production-ready evaluation and safety harness for healthcare RAG systems, built on 55,000 synthetic patient records. Covers accuracy measurement, cost-optimized model routing, and HIPAA-inspired compliance guardrails.

---

---

## Repository structure

```
healthcare-rag-guardrails/
├── data/
│   ├── healthcare_qa_200.json
│   ├── ragas_healthcare_results.json
│   ├── redteam_block_rate.json
│   └── router_results.json
├── evidence/
│   ├── AUDIT_LOG.md
│   └── PILLAR_COMPLIANCE.md
├── scripts/
│   ├── 01_gen_healthcare_qa.py
│   ├── 02_run_ragas_healthcare.py
│   ├── 03_classifier_router.py
│   ├── 04_pii_masker.py
│   ├── 05_llama_guard.py
│   └── 06_redteam_suite.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Overview

| Pillar | What was built | Key metric |
|---|---|---|
| **Evaluation** | Ragas eval harness — faithfulness + relevancy + context recall | faithfulness 0.96, relevancy 0.86 on 50 Q&A |
| **Cost analysis** | 3-tier classifier router (Haiku / Gemini Flash / Sonnet) | 62.2% cost reduction vs GPT-4 baseline |
| **Safety** | spaCy + regex PII masker + 50-prompt red-team suite | 1,753 PII tokens redacted · 100% block rate |

All numbers are real. Every script is reproducible. No hardcoded outputs.

---

## Architecture

```
Healthcare CSV (55K rows)
       │
       ▼
 BM25 Retriever ──── returns top-k context docs
       │
       ▼
 Claude Haiku ──────── generates answer from context
       │
       ▼
 Ragas Judge ───────── scores faithfulness / relevancy / recall
```

**Cost routing layer (parallel):**
```
Incoming query
       │
       ▼
 Complexity classifier (1 / 2 / 3)
       │
   ┌───┴──────────────┐
 Tier 1             Tier 2           Tier 3
 Claude Haiku    Gemini Flash    Claude Sonnet
 ($0.80/1M)      ($0.075/1M)     ($3.00/1M)
 simple facts    summaries       complex reasoning
```

**Compliance stack:**
```
Raw text → PII Masker (regex + spaCy NER) → sanitized text → RAG retriever
                                                    ↓
                              Red-team suite (50 adversarial prompts)
                              tests LLM safety layer directly
```

---

## Scripts

| Script | Purpose | Output |
|---|---|---|
| `01_gen_healthcare_qa.py` | Generate 100 Q&A pairs from CSV corpus | `data/healthcare_qa_200.json` |
| `02_run_ragas_healthcare.py` | BM25 retrieval + LLM generation + Ragas scoring | `data/ragas_healthcare_results.json` |
| `03_classifier_router.py` | Complexity classification + 3-tier cost routing | `data/router_results.json` |
| `04_pii_masker.py` | Regex + spaCy NER PII detection and redaction | `data/pii_masked_sample.json` |
| `05_llama_guard.py` | Secondary safety classifier (Llama Guard via Vertex) | `data/llama_guard_results.json` |
| `06_redteam_suite.py` | 50-prompt adversarial test suite | `data/redteam_block_rate.json` |

---

## Results (run 2026-04-20)

### Accuracy — `data/ragas_healthcare_results.json`
```
n_samples:         50
faithfulness:      0.9578
answer_relevancy:  0.8561
context_recall:    0.1275
retrieval:         BM25Okapi over 5,000 healthcare CSV rows
judge:             anthropic/claude-haiku-4-5 via OpenRouter
```

> Context recall (0.13) reflects BM25's keyword-match limit over raw CSV rows — not a model failure. Swapping BM25 for pgvector/Pinecone is the next retrieval layer. Faithfulness (0.96) confirms the generator stays grounded in whatever it retrieves.

### Cost — `data/router_results.json`
```
n_queries:          100
tier_distribution:  {simple: 32%, summary: 52%, complex: 16%}
baseline (GPT-4o):  $0.003922
routed cost:        $0.001484
cost_reduction:     62.2%
```

### Compliance — `data/pii_masked_sample.json` + `data/redteam_block_rate.json`
```
rows_processed:     500
total_redactions:   1,753
  PERSON (spaCy):   733
  ORG (spaCy):      528
  ZIP (regex):      402
  PHONE (regex):    39
  GPE (spaCy):      51

red_team_prompts:   50 (10 per category × 5 categories)
block_rate:         100%
categories tested:  pii_extraction · prompt_injection · jailbreak · prompt_leak · goal_hijack
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Required env vars
export OPENROUTER_API_KEY=...   # used for all LLM calls (claude-haiku-4-5)
```

### Run the full suite
```bash
python scripts/02_run_ragas_healthcare.py --n 50 --output data/ragas_healthcare_results.json
python scripts/03_classifier_router.py --queries data/healthcare_qa_200.json
python scripts/04_pii_masker.py --output data/pii_masked_sample.json
python scripts/06_redteam_suite.py --output data/redteam_block_rate.json
```

---

## Data

- **Corpus:** 55,501 synthetic patient records (not real PHI — Kaggle-sourced synthetic dataset)
- **Q&A:** 100 pairs generated directly from corpus values (factual, summary, reasoning, edge cases)
- **No real patient data is committed to this repo**

---

## Stack

- Python 3.12
- `ragas==0.2.6` — RAG evaluation
- `rank_bm25` — keyword retrieval
- `spacy` (en_core_web_sm) — NER for PII detection
- `openai` + OpenRouter — LLM API (model: anthropic/claude-haiku-4-5)
- `langchain-openai` — LangChain wrapper for Ragas LLM injection
- `datasets` — HuggingFace Dataset for Ragas input format
