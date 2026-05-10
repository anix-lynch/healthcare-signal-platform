"""
Step 3b — Llama Guard via Vertex AI Model Garden as secondary safety classifier.

Llama Guard is Meta's open-weights safety model that classifies prompts + responses
into harmful categories (violence, self-harm, sexual content, criminal planning, etc.).
In the guardrail stack, it acts as the second safety layer after the PII masker.

Vertex AI Model Garden supports Llama Guard as a self-deployed endpoint. For fast
iteration without deployment, use the Hugging Face alternative below.

Usage:
    python scripts/05_llama_guard.py \
        --input data/healthcare_qa_200.json \
        --output data/llama_guard_classifications.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def classify_via_vertex(prompt: str, project: str, location: str, endpoint_id: str | None = None):
    """If you've deployed Llama Guard 3 8B to a Vertex endpoint, call it here.
    Otherwise falls back to a prompt-based classifier using Gemini Flash."""
    import vertexai
    from vertexai.generative_models import GenerativeModel

    vertexai.init(project=project, location=location)

    if endpoint_id:
        # Direct Llama Guard endpoint call
        # from google.cloud import aiplatform
        # endpoint = aiplatform.Endpoint(endpoint_id)
        # return endpoint.predict(instances=[{"prompt": prompt}])
        raise NotImplementedError("Wire up Model Garden endpoint here when deployed")

    # Fallback: Gemini Flash acts as a safety classifier using the Llama Guard taxonomy
    model = GenerativeModel("gemini-1.5-flash")
    safety_prompt = f"""You are a safety classifier following the Llama Guard 3 taxonomy.

Categories:
  S1 Violent Crimes      S2 Non-Violent Crimes
  S3 Sex-Related Crimes  S4 Child Sexual Exploitation
  S5 Defamation          S6 Specialized Advice (medical/legal unsupervised)
  S7 Privacy             S8 Intellectual Property
  S9 Indiscriminate Weapons  S10 Hate
  S11 Suicide & Self-Harm  S12 Sexual Content
  S13 Elections           S14 Code Interpreter Abuse

Classify the prompt below. Return strict JSON:
  {{"verdict": "safe"|"unsafe", "categories": ["S7", ...]}}

PROMPT:
{prompt}"""

    resp = model.generate_content(
        safety_prompt,
        generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
    )
    try:
        return json.loads(resp.text)
    except json.JSONDecodeError:
        return {"verdict": "unknown", "categories": [], "raw": resp.text}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--project", default=os.getenv("GCP_PROJECT_ID"))
    parser.add_argument("--location", default=os.getenv("GCP_LOCATION", "us-central1"))
    parser.add_argument("--endpoint-id", default=None, help="Llama Guard Vertex endpoint ID if deployed")
    args = parser.parse_args()

    if not args.project:
        raise SystemExit("GCP_PROJECT_ID env var or --project flag required")

    items = json.loads(Path(args.input).read_text())
    if isinstance(items, dict) and "ledger" in items:
        items = items["ledger"]  # handle router_results shape

    classifications = []
    verdict_counts = {"safe": 0, "unsafe": 0, "unknown": 0}

    for i, item in enumerate(items):
        prompt = item.get("question") or item.get("query") or str(item)
        result = classify_via_vertex(prompt, args.project, args.location, args.endpoint_id)
        verdict = result.get("verdict", "unknown")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        classifications.append({"input": prompt[:200], **result})
        if (i + 1) % 20 == 0:
            print(f"  classified {i + 1} / {len(items)}")

    summary = {
        "n_classified": len(classifications),
        "verdict_distribution": verdict_counts,
        "safe_rate_pct": round(verdict_counts["safe"] / max(len(classifications), 1) * 100, 1),
        "classifier_backend": "vertex_endpoint" if args.endpoint_id else "gemini_flash_llamaguard_prompt",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"summary": summary, "classifications": classifications}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
