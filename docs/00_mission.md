# 00 — Mission

> *Clinical AI that saves lives without getting the hospital sued.*

---

## The whole company in one image

```
🟦  prepare data
       ↓
🟩  AI uses data
       ↓
🟥  governance watches AI
```

---

## The whole company in one line per layer

```
Layer 1  =  trusted data
Layer 2  =  useful AI
Layer 3  =  safe AI
```

That's it. Three layers, three jobs. Everything else is detail.

---

## Each layer as INPUT → OUTPUT

### 🟦  Layer 1 — Data Backbone

**INPUT:**

```
hospital chaos
- CSVs
- PDFs
- EHR / EMR
- billing
- schedules
- dirty tables
```

**OUTPUT:**

```
clean trusted healthcare data
- marts (bronze · silver · gold)
- APIs (OpenAPI contract)
- ML features (MLflow)
- dashboards (Power BI semantic model)
```

**Deliverable:** *"data the AI and business can actually use."*

---

### 🟩  Layer 2 — AI Application

**INPUT:**

```
clean healthcare context (from Layer 1)
+
patient / ops / exec request
```

**OUTPUT:**

```
AI decision / support
- NOW / SOON / WAIT triage
- chart-note draft
- routing recommendation
- anomaly flag
- KPI narrative briefing
```

**Deliverable:** *"AI that helps people do their jobs."*

---

### 🟥  Layer 3 — Governance

**INPUT:**

```
AI behavior
- prompts
- outputs
- evals
- logs
- adversarial attacks
- hallucinations
```

**OUTPUT:**

```
less dangerous AI
- blocked attacks (100% red-team baseline)
- eval reports (Ragas faithfulness 0.96)
- audit trail (7-year retention)
- compliance evidence (regulator-ready)
```

**Deliverable:** *"evidence the AI didn't go rogue."*

---

## The recruiter version (15 seconds)

```
Layer 1:   "we clean healthcare data."
Layer 2:   "we apply AI to healthcare workflow."
Layer 3:   "we evaluate and govern AI behavior."
```

That's the elevator pitch. Memorize it.

---

## Cross-references

- **Why each layer exists + ownership + role-to-folder map:** [`01_layer_purpose_and_ownership.md`](01_layer_purpose_and_ownership.md)
- **Operational realism (retry · timeout · audit · escalation):** [`02_operational_realism.md`](02_operational_realism.md)
- **What's shipped vs scaffold vs queued:** [`03_implementation_phases.md`](03_implementation_phases.md)
- **Architecture diagrams:** [`../diagrams/`](../diagrams/)
- **Patient lifecycle (12-step walkthrough):** [`../docs/05_patient_lifecycle.md`](../docs/05_patient_lifecycle.md)
