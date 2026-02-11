---
name: "Competitive Landscape & SERP Feature Ownership"
slug: "competitive-modeler"
version: "1.0.0"
tags: ["#competitors", "#serp", "#coverage", "#features", "#market-intelligence"]
summary: "Model topic coverage parity, identify content gaps and SERP feature opportunities against selected competitors using entity-based comparison."
---

## 1) Purpose

Quantify topical authority vs competitors; compute coverage per cluster; simulate SERP feature wins.

This skill defines:
- **Coverage parity matrix**
- **Opportunity heatmaps**
- **SERP feature simulator** (FAQ/HowTo/Review/Video etc.)

You use it to: benchmark breadth/depth, discover moats, target features.

## 2) Novelty rationale

Entity-level comparison (not keywords), intent-weighted coverage, deterministic snapshots.

## 3) Trigger conditions

**Use** competitive audits, niche evaluation; **Avoid** no competitor inputs or volatile news SERPs.

## 4) Prerequisites

SERP snapshots (`/cache/serp_*.html`), competitor list, reconciled entities.

## 5) Sources

- SERP feature docs
- Schema.org types
- TF-IDF/PageRank literature

## 6) Conceptual model

```
Our Clusters + Competitor Pages → Entity Intersection → Coverage & Feature Scores → Heatmap/Playbook
```

## 7) Procedure

1. Define competitors (`competitors.yaml`).
2. Extract competitor entities via NER + JSON-LD parsing.
3. Align by canonical IDs; compute overlap ratio per cluster.
4. Coverage: ours/total; gap = competitors - ours.
5. Feature sim: schema presence × relevance → potential.
6. Export: `coverage_matrix.csv`, `opportunity_heatmap.png`, `feature_playbook.md`.

## 8) Artifacts produced

- `coverage_matrix.csv`
- `opportunity_heatmap.png`
- `feature_playbook.md`

## 9) Templates

**coverage_matrix.csv**
```csv
cluster,entity,ours,competitors,coverage_score,gap
pricing,hörapparater,1,3,0.33,2
reviews,bästa hörapparater,1,2,0.5,1
bidrag,stöd hörapparater,0,1,0.0,1
```

## 10) Anti-patterns

- Treating nav/sitewide as coverage
- Mixing locales without labels
- Keyword vs entity conflation

## 11) Integration

- **Impact Forecaster**: prioritization
- **Programmatic Factory**: generate gaps
- **Schema Compiler**: plan schema for wins
- **Monitoring Agent**: track deltas
