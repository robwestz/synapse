---
name: "Effort→Impact Forecasting & Prioritization"
slug: "impact-forecaster"
version: "1.0.0"
tags: ["#forecast", "#planning", "#prioritization", "#roi", "#seo-strategy"]
summary: "Quantitative forecasting engine that converts entity-level metrics into prioritized content plans using deterministic effort→impact models and transparent assumption ledgers."
---

## 1) Purpose

Estimate traffic/conversions & ROI per entity/cluster under constraints; prioritize backlog with confidence bands and explainable assumptions.

This skill defines:
- **Assumptions ledger**
- **Effort→impact curves**
- **Budget allocator** (greedy/knapsack)
- **Confidence modeling**

You use it to: project gains, allocate hours/links, justify roadmaps.

## 2) Novelty rationale

Entity-driven, transparent, deterministic; multi-scenario ready.

## 3) Trigger conditions

**Use** quarterly/annual planning; **Avoid** <30d data.

## 4) Prerequisites

entity_metrics.parquet, optional coverage_matrix.csv, assumptions.yaml.

## 5) Sources

- CTR by rank (industry)
- Knapsack literature
- Forecasting basics

## 6) Conceptual model

```
Entity Metrics → CTR Curve → Potential → Effort/Cost → Optimize (budget) → Prioritized Backlog
```

## 7) Procedure

1. Load assumptions.yaml.
2. Base traffic: potential_clicks = impressions × ctr(rank); apply recovery for decay<0.
3. Effort: writer_hours, SME_hours, link_budget per difficulty.
4. Impact score = (potential × weight)/effort.
5. Optimize (knapsack).
6. Export: `backlog_prioritized.csv`, `assumptions.yaml`, `confidence_bands.json`.

## 8) Artifacts produced

- `backlog_prioritized.csv`
- `assumptions.yaml`
- `confidence_bands.json`

## 9) Templates

**assumptions.yaml**
```yaml
traffic_model:
  ctr_curve: "industry_default_v1"
  seasonality: none
effort_model:
  writer_hours_per_1k_words: 3
  sme_hours_per_brief: 1
  link_budget_per_month: 5
budget:
  writer_hours: 120
  sme_hours: 40
  months: 3
scenarios:
  base: 1.0
  optimistic: 1.3
  conservative: 0.7
```

## 10) Anti-patterns

- Brand CTR contamination
- Unit mismatch (clicks vs sessions)
- No confidence intervals

## 11) Integration

- **Programmatic Factory**: choose templates
- **Delivery DevOps**: scheduling by ROI
- **Monitoring Agent**: actual vs predicted
- **Quality Harness**: cost-benefit guardrails
