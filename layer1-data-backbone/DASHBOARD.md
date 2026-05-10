# DASHBOARD: Healthcare Analytics

Last updated: 2026-04-19

## What we're doing

Interview-ready healthcare DA stack: API (55K encounters) → dbt warehouse → Power BI semantic model → optional ML. Every resume claim in **sla** is traceable to code; proof lives in **outputs/**.

## Phase summary

| Phase | Status | Who |
| ----- | ------ | --- |
| P0 Context + keys | ✅ | AI |
| P1 Scaffold repair | ✅ | AI |
| P2 API proof | ✅ | AI |
| P3 dbt proof | ✅ | AI |
| P4 Semantic model proof | ✅ | AI |
| P5 ML proof | ✅ | AI |
| P9 Final interview lock | ✅ | Human |

Core proof phases done (see **SPEC.md** for P7/P8 optional polish).

## Flow

```
[API export] [Fabric profile] [TMDL] [ML snapshot]
       \           |            |          /
        +-> [ API + dbt + semantic model + ML ] ->+
                                                  v
[api_proof] [dbt_proof] [bi_proof] [ml_proof] [resume_proof]
```

Progress and file map: **SPEC.md**.
