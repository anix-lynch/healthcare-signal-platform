"""
L1.5 Signal Console — Cloud Run entrypoint.

Demonstrates the AI-Platform thesis: signals are computed BEFORE the agent (L1.5),
fed in as LABELED fields, and the L2 agent reasons on those labels — never raw
data. Serves a console UI (/) + JSON (/api/signals) + a live Gemini decision
(/api/decide) that narrates the L1 facts + L1.5 signals into an L2 recommendation.

Signal metrics are the real numbers from the eval harness
(layer2-ai-application/shared/evaluation/*_eval.py); see signals.json provenance.
Runtime auth = Cloud Run service identity (bchan-genai-deploy@, Vertex AI User).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE = Path(__file__).resolve().parent
SIGNALS = json.loads((BASE / "signals.json").read_text())
CASES = {c["id"]: c for c in SIGNALS["cases"]}

_PROJECT = os.environ.get("GCP_PROJECT_ID", "bchan-genai-lab")
_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
_MODEL = os.environ.get("SIGNAL_MODEL", "gemini-2.5-flash")

# Langfuse — L2 LLM observability. Optional + fully defensive: if keys are absent
# or the SDK errors, the agent decision still returns. Never let tracing break L1.5.
try:
    from langfuse import Langfuse
    _LF = Langfuse() if os.environ.get("LANGFUSE_PUBLIC_KEY") else None
except Exception:
    _LF = None

app = FastAPI(title="L1.5 Signal Console", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def home():
    idx = BASE / "web" / "index.html"
    if not idx.exists():
        raise HTTPException(404, "UI not built")
    return FileResponse(idx)


@app.get("/healthz")
def healthz():
    return {"ok": True, "cases": list(CASES)}


@app.get("/api/signals")
def api_signals():
    return SIGNALS


@app.get("/api/decide")
def api_decide(case: str, signals: bool = True):
    """L2 agent decision. signals=true → reasons on L1 facts + L1.5 signal labels.
    signals=false → ABLATION: same agent, raw L1 facts only (no signals). The delta
    between the two is the proof that the L1.5 layer changes the action."""
    c = CASES.get(case)
    if not c:
        raise HTTPException(404, f"unknown case '{case}'")

    facts = "\n".join(f"- {k}: {v}" for k, v in c["truth"].items())
    sigs = "\n".join(f"- {s['name']}: {s['value']} (severity={s['tone']})" for s in c["signals"])

    if signals:
        prompt = (
            "You are an L2 agent in a healthcare AI platform. You reason ONLY on the "
            "L1 facts and the PRE-COMPUTED L1.5 signal labels below — you do not compute "
            "signals yourself, you consume them. In 3-4 sentences, give a single clear "
            "recommendation and justify it by citing specific signals by name. End with "
            "the action in the form 'Action: <verb> ...'.\n\n"
            f"Audience: {c['audience']}\n\nL1 facts (trusted warehouse):\n{facts}\n\n"
            f"L1.5 signals (labeled, pre-computed):\n{sigs}\n\nRecommendation:"
        )
    else:
        prompt = (
            "You are an L2 agent in a healthcare AI platform. You have ONLY the raw L1 "
            "facts below — no pre-computed signals. In 3-4 sentences, give a single clear "
            "recommendation. End with the action in the form 'Action: <verb> ...'.\n\n"
            f"Audience: {c['audience']}\n\nL1 facts (trusted warehouse):\n{facts}\n\nRecommendation:"
        )
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig

        vertexai.init(project=_PROJECT, location=_LOCATION)
        model = GenerativeModel(_MODEL)

        gen = None
        if _LF is not None:
            try:
                gen = _LF.start_observation(
                    name="signal-decide", as_type="generation", model=_MODEL,
                    input=prompt,
                    metadata={"case": case, "audience": c["audience"], "signals_used": signals},
                )
            except Exception:
                gen = None

        resp = model.generate_content(
            prompt, generation_config=GenerationConfig(temperature=0.0, max_output_tokens=2048)
        )
        text = (resp.text or "").strip()

        if gen is not None:
            try:
                gen.update(output=text)
                gen.end()
                _LF.flush()
            except Exception:
                pass

        return {"case": case, "grounded": True, "model": _MODEL, "decision": text,
                "signals_used": signals, "observed": gen is not None}
    except Exception as exc:
        return {
            "case": case, "grounded": False, "model": _MODEL,
            "decision": c["agent_says"],  # deterministic fallback from the case
            "note": f"{type(exc).__name__}: {exc}",
        }
