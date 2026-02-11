# TAA Routing Examples

## Topical Plan
Prompt:
- taa plan --topic "hörapparater" --format md

LLM Route:
- entity-reconciler → (return knowledge_graph.json, topic_clusters.json, content_plan.csv, internal_linking.md, briefs/*.md)

## Competitive Audit
Prompt:
- taa run --skills [competitive-modeler] --format table

LLM Route:
- entity-reconciler → competitive-modeler → (return coverage_matrix.csv, feature_playbook.md)

## ROI Forecast
Prompt:
- taa run --skills [first-party-ingest, impact-forecaster] --format csv

LLM Route:
- first-party-ingest → impact-forecaster → (return backlog_prioritized.csv)
