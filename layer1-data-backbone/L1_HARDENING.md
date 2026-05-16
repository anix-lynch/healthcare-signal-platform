# L1 Hardening — From Clean Meal Prep → Surviving Real-World Groceries

> **Where we are:** L1 is **GenAI-friendly** — covers the 7 patterns' field needs.  
> **Where we are NOT:** L1 is **not real-life realistic** yet.  
> **Next upgrade:** real-world ingestion disguise. Same canonical contract on the other side.

---

## Current state (audit pass, 2026-05-16)

```
GENAI READINESS         ✅ pass — 7 patterns can chew on the enriched 497-row corpus
REAL-LIFE REALISM       ❌ fail — data arrives as one clean CSV, not hospital chaos
```

Right now L1 = **clean meal prep**. The 497 enriched rows look like a hospital
already pre-chewed everything, JSON-encoded it, and handed it over with a bow.
That's enough for Layer 2 patterns to develop against. It is **not** what an
actual hospital data engineer faces on day one.

---

## What real life actually looks like 😭

```
Hospital data engineer's Monday morning:
─────────────────────────────────────────────────────────────────────
└── EHR exports     → 8 different CSVs from 4 different vendors, no schema docs
└── discharge notes → PDFs in SharePoint, scanned + OCR'd + typo'd
└── nurse handoffs  → JSONL from a custom tool, free-text, inconsistent
└── policy docs     → DOCX from compliance, mixed with screenshots
└── billing exports → Excel with merged cells, "N/A" as string, no dates
└── lab feeds       → HL7 messages dropped on FTP every 4 minutes (ignored for now)
─────────────────────────────────────────────────────────────────────

Right now L1 is clean meal prep.
Next upgrade:
make L1 survive groceries arriving
in plastic bags, receipts, PDFs, and cursed Excel 😭
```

---

## Next upgrade scope (deliberately small)

**Goal:** prove L1 can turn real-world file chaos into the same AI-ready contract.

**NOT the goal:** perfect hospital ETL with FHIR/HL7 ingestion. That's a 6-month
project. We're doing the 2-day demo version that PROVES the architecture survives
diverse sources.

### File chaos to add

```
layer1-data-backbone/
└── source_systems/                 ← NEW
    ├── csv/
    │   └── encounters_raw.csv      messy export with inconsistent headers
    ├── pdf/
    │   ├── discharge_summary_001.pdf   synthetic discharge note
    │   └── triage_note_002.pdf         synthetic triage scribble
    ├── notes/
    │   └── nurse_notes.jsonl       free-text shift handoffs
    └── sharepoint_export/
        └── policy_guidelines.md    clinical protocol prose
```

### Scripts to add

```
scripts/
├── ingest_csv.py              messy CSV → typed rows + audit_lineage
├── ingest_pdf.py              pdfplumber + simple regex extract
├── ingest_notes.py            JSONL handoffs → patient_id resolved rows
└── normalize_to_canonical.py  union all sources → canonical_patient_context
                                (the output L2 already consumes today)
```

Each ingest script:
- writes to a staging table
- records `source_system`, `ingest_ts`, `row_hash`, `pii_redaction_status`
  in `audit_lineage_view`
- never blocks Layer 2 (L2 reads from canonical_patient_context, not raw sources)

---

## The L1 OUTPUT CONTRACT (frozen — L2 depends on this shape)

This is the contract Layer 2 already consumes. **Adding new ingestion paths must
NOT change this shape.** New sources land in `source_systems/`, get normalized
into `canonical_patient_context`, and downstream patterns are unaware.

```
L1_OUTPUT_CONTRACT
│
├── canonical_patient_context          ← The fact table L2 reads
│   ├── encounter_id                    Rachel + Crystal Ball + Police Lineup
│   ├── patient_id                      Rachel guard + identity audit
│   ├── chief_complaint                 Traffic Light + Rachel snippet
│   ├── hpi                             Mad Lib grounding + Rachel snippet
│   ├── vitals                          Traffic Light + Smoke Detector
│   ├── lab_flags                       Smoke Detector + Crystal Ball features
│   ├── diagnosis_family                Treasure Map clustering
│   ├── medication_summary              Crystal Ball features
│   ├── outcome                         Crystal Ball target + Mad Lib disposition
│   └── source_refs                     [{source_id, source_type, ingest_ts}]
│
├── retrieval_corpus_view              ← Rachel reads this
│   ├── source_id                       L1-NNNNNN | GUIDE-* | POLICY-*
│   ├── patient_id                      enables cross-patient leak guard
│   ├── encounter_id
│   ├── doc_text                        rendered snippet ready for BM25/dense
│   ├── source_type                     past_case | guideline | protocol
│   ├── clinical_bucket                 enables clinical_recall@K eval metric
│   └── timestamp
│
├── feature_view                       ← Crystal Ball + Smoke Detector read this
│   ├── predicted_los_features          age, condition, admission_type, season
│   ├── readmission_features            prior_visits, comorbidity_proxy
│   ├── mortality_features              age, condition, acuity_red_flags
│   └── ops_capacity_features           bed_pressure, ER_utilization, staffing
│
├── eval_holdout_view                  ← Layer 3 eval reads this
│   ├── query                           rendered question or case dump
│   ├── relevant_ids                    ground-truth source_ids
│   ├── graded_relevance                {source_id: 0|1|2|3}
│   └── query_bucket                    enables ClinicalRecall@K
│
└── audit_lineage_view                 ← Compliance + drift reads this
    ├── source_system                   csv | pdf | notes | sharepoint | direct
    ├── ingest_ts                       when this row landed
    ├── transform_version               which normalize_to_canonical.py shipped it
    ├── row_hash                        sha256 of canonical row for change detection
    └── pii_redaction_status            cleared | partial | needs_review
```

---

## Pattern → field needs map

This is **what each L2 pattern depends on**. Use it as a contract test: if any
ingestion path drops a field, the matching pattern will start hallucinating.

```
PATTERN          NEEDS FROM L1 (must survive any ingestion path)
─────────────────────────────────────────────────────────────────────
🔍 Rachel        clinical narrative (HPI + CC + physician_note)
                 + patient_id (cross-patient leak guard)
                 + source_id (citation validation)
                 + clinical_bucket (ClinicalRecall@K eval metric)

🚦 Traffic Light chief_complaint + vitals (BP/HR/RR/T/SpO2)
                 + acuity_red_flags
                 + esi_tier_truth (eval only, NEVER as feature)

🔮 Crystal Ball  LoS target (length_of_stay_days)
                 + readmission target (is_readmission)
                 + risk features (age, condition, prior_visits, vitals)
                 — NO discharge-time fields at predict time (leakage guard)

📖 Mad Lib       Rachel citations (source_id list)
                 + guideline text (retrieval_corpus_view, source_type=guideline)
                 + physician_note as grounding ceiling

🚨 Smoke Detector baseline distribution per cohort
                 + anomaly_score-able fields (vitals, lab values)
                 + outlier_reasons hooks

🗺️ Treasure Map  clusterable patient features
                 (demographics + condition family + admission pattern + outcome)
                 + cluster_label for human-readable phenotype names

👮 Police Lineup graded_relevance from eval_holdout_view
                 + evidence_scores per source_id
                 + the Rachel hits to rerank over
```

---

## Roadmap order (do NOT skip steps)

```
PHASE A — current (DONE 2026-05-16)
   ✅ L1 emits clean canonical_patient_context for 497 rows
   ✅ L2 patterns all consume it
   ✅ identity bridge wired for Rachel cross-patient guard
   ✅ holdout split preserved (100 rows, never trained on)

PHASE B — small ingestion realism (NEXT, 2-3 days)
   ⌛ source_systems/ folder with 1 sample each: csv, pdf, notes, sharepoint
   ⌛ 4 ingest_*.py scripts
   ⌛ normalize_to_canonical.py union pipeline
   ⌛ audit_lineage_view populated
   ⌛ existing canonical_patient_context unchanged (contract frozen)

PHASE C — light-touch real-world hardening (1-2 weeks)
   ⌛ PII redaction at ingest time (spaCy + regex), not just runtime
   ⌛ schema validation per source (Pydantic at ingest, not just downstream)
   ⌛ source freshness SLA tracking (last_ingest_ts per source_system)
   ⌛ dbt tests for canonical_patient_context completeness

PHASE D — production-grade EHR (deferred, 1-3 months)
   ❌ FHIR / HL7 message ingestion (real EHR feed)
   ❌ probabilistic entity resolution (rapidfuzz / SPLINK)
   ❌ change data capture from live EHR
   ❌ MRN-based identity (replaces name-hash patient_id)
   ❌ Synthea-grade synthetic generator OR PhysioNet credential
```

**Why this order:**
- Layer 2 is built and Layer 3 eval baselines exist. If we change the L1
  contract now, BOTH layers regress.
- Phase B teaches the SAME contract a new trick (source diversity). No L2
  changes.
- Phase D is when realism actually pays for itself, but only after the
  contract has survived Phase B + C without drift.

---

## Brutal one-liner

```
Right now L1 is clean meal prep.
Next upgrade:
   make L1 survive groceries arriving in
   plastic bags, receipts, PDFs, and cursed Excel 😭
```

---

## Cross-references

- L1 README (current shipped state): [`README.md`](README.md)
- L2 pattern scaffolds (consumers of this contract): `../layer2-ai-application/shared/`
- L1 honest gaps audit: [`../docs/03_implementation_phases.md`](../docs/03_implementation_phases.md)
- Full lifecycle (where the contract is enforced): [`../docs/05_patient_lifecycle.md`](../docs/05_patient_lifecycle.md)
