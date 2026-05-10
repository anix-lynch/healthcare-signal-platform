# _archive

> Stuff that's preserved but **not on the active code path**. Don't read these to understand the system today — read the active layers above.

---

## Why this folder exists

Repos accumulate. Pre-monorepo legacy docs, AI-generated tooling junk (Spec-Kit agents/prompts), recruiter bundles, dated proofs. None of it should sit next to the live code where a recruiter scrolling the tree gets confused about what's current.

This folder keeps that history intact (git blame stays clean, links don't 404) without polluting the architect's-eye view of `layer1` / `layer2` / `layer3`.

## What's in here

```
layer1/
   ├── README.legacy.md              pre-monorepo standalone README (15K, kept for reference)
   ├── SPEC.md                       pre-monorepo engineering spec
   ├── DASHBOARD.md · SCREENSHOTS.md  legacy overview docs
   ├── sla.md · sla_all_roles.md     pre-monorepo SLA + claim-to-code traceability
   ├── fabric_April20.md             dated memo
   ├── .instructions.md              Spec-Kit AI artifact
   ├── dot_github_speckit/           Spec-Kit AI-generated agents + prompts (18 files)
   ├── fabric_april/                 Microsoft Fabric proof-of-work bundle (April)
   ├── headhunter_ready/             recruiter-facing artifacts (better lives on gozeroshot.dev)
   ├── screenshots/                  image proofs (PNG)
   ├── scripts_legacy/               proof-rendering scripts
   └── outputs_md_proofs/            markdown 'proof' docs from layer1/outputs/
```

## Rules

- **Don't link to anything in here from active docs.** If you need it active, move it back.
- **Don't delete.** Git history would still hold it, but the file-tree breadcrumb is useful.
- **Don't add to it casually.** Things land here when they were once active and are now superseded — not as a junk drawer for new work.
