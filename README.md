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

- `signal-console/` — the live ablation console **(flagship)**
- `layer2-ai-application/shared/` — the signal services (anomaly · classify · cluster · rank · retrieval)
- `layer1-data-backbone/` · `layer3-governance/` — the data and governance layers that feed and guard the signals

## Quick start

```bash
cd layer2-ai-application && pip install -r requirements.txt
make eval-all        # run the signal evals against the golden set
```

## Stack

Python · FastAPI · scikit-learn · Vertex AI (Gemini) · BM25 · Weights & Biases · Langfuse · Cloud Run · Docker

---
*Synthetic data, no PHI. Layers integrate by mission today; the live L1→L2 data pipeline is queued. Part of Anix Lynch's L1→L3 healthcare AI platform — [gozeroshot.dev](https://gozeroshot.dev). MIT licensed.*
