# healthcare-signal-platform

> **L1.25 + L1.5 healthcare AI platform.** Patient features and *evaluated* signals — anomaly, cluster, classify, rank, retrieval — computed **before** the agent and fed in as labeled facts. Trusted data → features → signals → the signals measurably change the agent's decision → an accountable human signs off.

### ▶︎ Flagship — the live Signal Console

**[signal-console-819957310168.us-west1.run.app](https://signal-console-819957310168.us-west1.run.app)**

Pick a case and watch the *same* agent decide **with** the signals vs **without** them. The recommendation visibly flips (WATCH → ACT NOW). That's the whole thesis: signals change the decision, they don't decorate it.

## What it proves

- **Signals change decisions, not decoration** — an on-screen ablation flips the agent's call when the signals are removed.
- **Every signal is evaluated** — anomaly **F1 0.85**, cluster **silhouette 0.41** (535 high-utilizers in 40K), classify **±1-tier 100%** — each scored against an industry benchmark (🟢/🟡), logged in [Weights & Biases](https://wandb.ai/alynch-zeroshot/healthcare-l15-signals), agent calls traced in Langfuse.
- **Computed before the agent** — each signal is a labeled field (`{anomaly_score, cluster, esi_tier}`); the Gemini agent reasons on the labels, never recomputes them — no context pollution.
- **Synthetic data, real methods** — no PHI; every eval number is on a synthetic set.

## Structure

- `layer2-ai-application/shared/` — **the signals themselves.** One folder per algorithm (`anomaly` · `classify` · `cluster` · `rank` · `retrieval`); read these to see exactly how each signal is built and evaluated.
- `signal-console/` — the live ablation console **(flagship)**: `main.py` serves the API, `signals.json` holds the computed signals + their eval numbers, `web/` is the UI.
- `layer1-data-backbone/data/` — the synthetic patient dataset the signals run on.

## Quick start

```bash
pip install -r layer2-ai-application/requirements.txt

# How a signal is built → read one folder, e.g. the high-utilizer cohort:
#   layer2-ai-application/shared/cluster/cohort.py   (reproduces silhouette 0.41, 535 cohort)
# How it's served → signal-console/ (FastAPI + the ablation UI; deploys on Cloud Run)
```

## Stack

Python · FastAPI · scikit-learn · Vertex AI (Gemini) · BM25 · Weights & Biases · Langfuse · Cloud Run · Docker

---
*Synthetic data, no PHI. The broader L1 data-warehouse and L3 governance work lives in sibling repos. Part of Anix Lynch's L1→L3 healthcare AI platform — [gozeroshot.dev](https://gozeroshot.dev). MIT licensed.*
