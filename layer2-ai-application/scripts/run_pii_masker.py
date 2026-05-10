"""
Step 3a — HIPAA-inspired PII masker.

Combines:
  - Regex for structured PII (SSN, DOB, phone, email, MRN)
  - spaCy NER for names + locations

Usage:
    python -m spacy download en_core_web_sm   # once
    python scripts/04_pii_masker.py \
        --input healthcare_da_src/data/raw/sample_patient.json \
        --output data/pii_masked_sample.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PII_PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "SSN_nodash": re.compile(r"\b\d{9}\b"),
    "DOB": re.compile(r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b"),
    "PHONE": re.compile(r"\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "MRN": re.compile(r"\bMRN[-:\s]*\d{6,10}\b", re.IGNORECASE),
    "ZIP": re.compile(r"\b\d{5}(-\d{4})?\b"),
    "CREDIT_CARD": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
}


def mask_regex(text: str) -> tuple[str, dict]:
    """Apply regex patterns, return masked text + hit counts."""
    hits = {}
    for label, pat in PII_PATTERNS.items():
        matches = pat.findall(text)
        if matches:
            hits[label] = len(matches)
            text = pat.sub(f"[REDACTED_{label}]", text)
    return text, hits


def mask_ner(text: str, nlp) -> tuple[str, dict]:
    """Use spaCy NER to mask names + locations."""
    doc = nlp(text)
    hits = {}
    # Replace in reverse order so offsets stay valid
    ents = sorted(doc.ents, key=lambda e: -e.start_char)
    for ent in ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "ORG"}:
            label = ent.label_
            hits[label] = hits.get(label, 0) + 1
            text = text[:ent.start_char] + f"[REDACTED_{label}]" + text[ent.end_char:]
    return text, hits


def mask_all(text: str, nlp) -> dict:
    regex_masked, regex_hits = mask_regex(text)
    fully_masked, ner_hits = mask_ner(regex_masked, nlp)
    return {
        "masked_text": fully_masked,
        "regex_hits": regex_hits,
        "ner_hits": ner_hits,
        "total_pii_redactions": sum(regex_hits.values()) + sum(ner_hits.values()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file or plain text file")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise SystemExit("Run: python -m spacy download en_core_web_sm")

    input_path = Path(args.input)
    raw = input_path.read_text()

    # For large CSV files: process row by row instead of whole file
    import csv, io
    try:
        data = json.loads(raw)
        def walk(obj, path=""):
            if isinstance(obj, str):
                return mask_all(obj, nlp)
            if isinstance(obj, dict):
                return {k: walk(v, f"{path}.{k}") for k, v in obj.items()}
            if isinstance(obj, list):
                return [walk(v, f"{path}[{i}]") for i, v in enumerate(obj)]
            return obj
        masked = walk(data)
    except json.JSONDecodeError:
        # CSV path: process first 500 rows, aggregate hit counts
        reader = csv.DictReader(io.StringIO(raw))
        total_regex_hits: dict = {}
        total_ner_hits: dict = {}
        total_redactions = 0
        rows_processed = 0
        sample_rows = []
        for row in reader:
            if rows_processed >= 500:
                break
            row_text = " ".join(str(v) for v in row.values())
            result = mask_all(row_text, nlp)
            total_redactions += result["total_pii_redactions"]
            for k, v in result["regex_hits"].items():
                total_regex_hits[k] = total_regex_hits.get(k, 0) + v
            for k, v in result["ner_hits"].items():
                total_ner_hits[k] = total_ner_hits.get(k, 0) + v
            if rows_processed < 5:
                sample_rows.append({"original_preview": row_text[:200], "masked_preview": result["masked_text"][:200]})
            rows_processed += 1
        masked = {
            "rows_processed": rows_processed,
            "total_pii_redactions": total_redactions,
            "regex_hits_by_type": total_regex_hits,
            "ner_hits_by_type": total_ner_hits,
            "sample_rows": sample_rows,
            "note": f"Processed first {rows_processed} rows of {input_path.name}",
        }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(masked, indent=2))
    print(f"Wrote masked output to {output_path}")


if __name__ == "__main__":
    main()
