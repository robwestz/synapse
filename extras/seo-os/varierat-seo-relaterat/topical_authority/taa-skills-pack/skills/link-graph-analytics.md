---
name: "Link Graph Analytics & Flow Modeling"
slug: "link-graph-analytics"
version: "1.0.0"
tags: ["#links", "#internal-linking", "#pagerank", "#anchor-text", "#flow"]
summary: "Analyze internal and external link graphs to measure link flow, anchor entropy, and decay, visualizing authority transfer within and across clusters."
---

## 1) Purpose

Quantify internal link equity and anchor diversity. Detect decay, orphans, and underlinked nodes.

This skill defines:
- **Graph metrics** (PageRank, betweenness)
- **Anchor normalization & entropy**
- **Decay tracking** (Δ edges)
- **Cross-cluster flow maps**

You use it to: optimize internal linking, monitor authority flow.

## 2) Novelty rationale

Entity-level link semantics, not just link counts.

## 3) Trigger conditions

**Use** link audits, redesign validation; **Avoid** incomplete structures.

## 4) Prerequisites

internal_linking.md, knowledge_graph.json, optional crawl.

## 5) Sources

- PageRank paper
- Moz equity modeling
- Case studies

## 6) Conceptual model

```
Links → Build Graph → Compute Flow/Entropy → Recommendations
```

## 7) Procedure

1. Parse all hub↔spoke and cross-cluster links.
2. Build weighted digraph (anchor relevance × position).
3. Compute PageRank, betweenness, anchor entropy, link decay.
4. Export: `graph_metrics.csv`, `decay_report.csv`, `recommendations.md`.

## 8) Artifacts produced

- `graph_metrics.csv`
- `decay_report.csv`
- `recommendations.md`

## 9) Templates

**graph_metrics.csv**
```csv
entity,cluster,pagerank,anchor_entropy,inbound,outbound
horapparater,main,0.123,0.78,10,12
basta_horapparater,reviews,0.084,0.55,7,5
```

## 10) Anti-patterns

- Ignoring anchor quality
- Sitewide nav distortion
- Mixing internal/external flows

## 11) Integration

- **Monitoring Agent**: decay alerts
- **Impact Forecaster**: authority inputs
- **Schema Compiler**: snippet prioritization
