"""
Step 1a — Generate 200+ healthcare Q&A pairs from the healthcare corpus.

FIXED 2026-04-20: Uses OpenAI gpt-4o-mini instead of Vertex Gemini.
Vertex version intact but requires gcloud auth — use --provider vertex if GCP authed.

Run:
    python scripts/01_gen_healthcare_qa.py \
        --corpus healthcare_da_src/data/raw \
        --n 200 \
        --output data/healthcare_qa_200.json

Evidence: data/healthcare_qa_200.json → fed into script 02 for Ragas eval
Pillar: 🎯 ACCURACY
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


PROMPT_TMPL = """You are generating a healthcare RAG evaluation benchmark.

Below are rows from a 55K synthetic patient records dataset (no real PHI).
Generate {n} diverse question-answer pairs that a clinical RAG system should handle.

Requirements:
- Question must be answerable from the provided data
- Answer must be factually derivable from the rows below
- Mix: ~40% factual lookup, ~30% summarization, ~20% reasoning, ~10% edge cases
- Return strict JSON array: [{{"question": "...", "ground_truth_answer": "...", "category": "factual|summary|reasoning|edge"}}]

DATA SAMPLE:
{corpus}
"""


def load_corpus_sample(corpus_dir: Path, max_rows: int = 200) -> str:
    """Load CSV rows as text for Q&A generation context."""
    import csv
    rows = []
    for csv_file in corpus_dir.glob("**/*.csv"):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(json.dumps(row))
        if rows:
            break
    return "\n".join(rows[:max_rows])


def generate_with_openai(client, corpus_text: str, n: int) -> list[dict]:
    """Generate Q&A pairs using OpenAI gpt-4o-mini."""
    batch_size = 25
    all_qa = []
    for batch_start in range(0, n, batch_size):
        batch_n = min(batch_size, n - batch_start)
        prompt = PROMPT_TMPL.format(n=batch_n, corpus=corpus_text[:30_000])
        print(f"  Generating batch {batch_start // batch_size + 1} ({batch_n} Q&As)...")
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            raw = resp.choices[0].message.content
            parsed = json.loads(raw)
            # Handle wrapped array
            if isinstance(parsed, dict):
                qa = next((v for v in parsed.values() if isinstance(v, list)), [])
            else:
                qa = parsed
            all_qa.extend(qa)
            print(f"  Batch done: {len(qa)} Q&As (total so far: {len(all_qa)})")
        except Exception as e:
            print(f"  Batch error: {e}")
        time.sleep(0.5)
    return all_qa


def generate_with_vertex(corpus_text: str, n: int, project: str, location: str) -> list[dict]:
    """Generate Q&A pairs using Vertex Gemini 1.5 Pro (requires gcloud auth)."""
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project=project, location=location)
    model = GenerativeModel("gemini-1.5-pro")
    batch_size = 50
    all_qa = []
    for batch_start in range(0, n, batch_size):
        batch_n = min(batch_size, n - batch_start)
        prompt = PROMPT_TMPL.format(n=batch_n, corpus=corpus_text[:120_000])
        print(f"  Generating batch {batch_start // batch_size + 1} via Vertex...")
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7, "response_mime_type": "application/json"},
        )
        try:
            qa = json.loads(resp.text)
            if isinstance(qa, dict):
                qa = next((v for v in qa.values() if isinstance(v, list)), [])
            all_qa.extend(qa)
        except json.JSONDecodeError as e:
            print(f"  Parse error: {e}")
        time.sleep(0.2)
    return all_qa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="healthcare_da_src/data/raw")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--output", default="data/healthcare_qa_200.json")
    parser.add_argument("--provider", choices=["openai", "vertex"], default="openai",
                        help="openai (default, key from env) or vertex (needs gcloud auth)")
    parser.add_argument("--project", default=os.getenv("GCP_PROJECT_ID"))
    parser.add_argument("--location", default=os.getenv("GCP_LOCATION", "us-central1"))
    args = parser.parse_args()

    corpus_dir = Path(args.corpus)
    print(f"Loading corpus from {corpus_dir}...")
    corpus_text = load_corpus_sample(corpus_dir)
    print(f"Corpus sample: {len(corpus_text)} chars from {corpus_dir}")

    if args.provider == "openai":
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        all_qa = generate_with_openai(client, corpus_text, args.n)
    else:
        if not args.project:
            raise SystemExit("--project or GCP_PROJECT_ID required for vertex provider")
        all_qa = generate_with_vertex(corpus_text, args.n, args.project, args.location)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_qa, indent=2))

    print(f"\n✅ Wrote {len(all_qa)} Q&A pairs to {output_path}")
    print(f"   Categories: {set(q.get('category', 'unknown') for q in all_qa)}")
    print(f"   Next: python scripts/02_run_ragas_healthcare.py --qa {args.output} --output data/ragas_healthcare_results.json")


if __name__ == "__main__":
    main()
