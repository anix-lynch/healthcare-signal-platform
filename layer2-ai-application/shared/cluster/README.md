# Pattern 6 — cohort clustering 🗺️

> **"what suffering tribe is this 😭"**

Phenotype clustering. Groups cases by similarity in feature space so an
ops dashboard can show "we have N geriatric_polypharm_chest_pain today,
Y young_chemo_neutropenic, Z asthma_exacerbation".

## File map

```
shared/cluster/
├── __init__.py        public API (assign_cluster, TreasureMapOutput)
├── schema.py          Pydantic output contract
├── baseline.py        wraps cohort.cluster_cases() → TreasureMapOutput
├── cohort.py          k-means engine + silhouette (existing, working)
└── README.md          you are here
```

## What's shipped

```
k-means over 55K corpus       ✅ shipped (k=4 default)
silhouette scoring             ✅ shipped (engine returns it)
cluster naming heuristic       ✅ shipped (engine's _name_cluster)
predict_one() for new case     ❌ queued (engine doesn't expose nearest-centroid)
HDBSCAN alternative            ❌ queued
calibration on holdout         ❌ queued
```

## The brutal mantra

```
k=2 → "sick" vs "well"             — trivial
k=4 → 4 reasonable phenotypes      — current default
k=8 → over-fits the 55K registry   — silhouette drops
k=adaptive (HDBSCAN) = lets data choose; right answer for production
```

## Together with the other patterns

```
retrieval: "this smells like 5 past cases"
cohort clustering: "...all of which are in the same cluster_3
                = elderly_polypharm_chest_pain phenotype"
                → ops dashboard groups them for routing
forecast: predicts the LoS for this PHENOTYPE
                = tighter cohort = sharper number
```

Without cohort clustering, "similar cases" is a flat list. With it, similar
cases come with a NAME that an ops manager can act on.

## Quick start

```python
from shared.cluster import assign_cluster

case = {
    "Medical Condition": "Cancer",
    "Age": "67",
    "Admission Type": "Urgent",
}
out = assign_cluster(case, case_id="CASE-104")
print(out.model_dump_json(indent=2))
```
