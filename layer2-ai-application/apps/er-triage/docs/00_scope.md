# ER3 Scope

## In scope (shipping now)

- **Phase 2:** ESI tier auto-tagger (`app/classify/`)
- **Phase 2 safety:** Safety Agent hard-rule overlay (`app/safety/`)
- **Phase 3:** Centroid-shift drift monitor (`app/anomaly/drift.py`)
- **Phase 3:** Per-case anomaly flagger (`app/anomaly/anomaly_flagger.py`)
- Smoke tests (must pass for CI green)
- Hand-labeled 30-case ESI golden set

## Out of scope (parking lot)

- **Phase 4:** Police Lineup cross-encoder rerank — wait for >10k cases
- **Phase 5:** Treasure Map presentation cohorts — wait for ops dashboard ask
- **Phase 6:** Crystal Ball length-of-stay regression — wait for bed-mgmt ask
- New UI (uses ER2's existing Streamlit)
- New deployment (ER3 modules plug into ER2's Cloud Run when ready)

## Why two phases at once

Phase 2 alone gives auto-tagging speed. Phase 3 alone gives drift safety.
Together they unlock all 5 Nora Bing pillars from day one — accuracy +
speed + cost + compliance + innovation. Shipping them together avoids
a half-built system that's compliant in nothing.

## What "done" looks like for v0.1

- All smoke tests green
- 95%+ accuracy on golden ESI set (within ±1 tier)
- Safety overrides verified for all 4 red-flag categories
- Drift monitor fires correctly on synthetic 30% perturbation
- One end-to-end demo: case in → classifier → safety → drift logged
