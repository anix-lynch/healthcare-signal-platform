# Input Context: Semantic Model Bundle

**What goes IN:** TMDL definition of the semantic model (tables, relationships, measures). Source for Fabric deployment and validation.

Expected filename: healthcare_semantic_model_v1.tmdl

How to get it:
1. Export or copy the current semantic model package from powerbi-model/.
2. Keep naming aligned with release candidate version.

How agent uses it:
- Cross-checks relationships and KPI definitions against dbt marts.
