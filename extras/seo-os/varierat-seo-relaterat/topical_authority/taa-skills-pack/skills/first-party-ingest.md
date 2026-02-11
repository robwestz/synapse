---
name: "First-Party Ingest & Entity Mapping"
slug: "first-party-ingest"
version: "1.0.0"
tags: ["#ga4", "#gsc", "#logs", "#entities", "#automation", "#seo-intelligence"]
summary: "Collect, normalize, and map GA4, GSC, and log data to entities in the knowledge graph. Surfaces cannibalization, decay, and opportunity scores for each entity, feeding TAA's prioritization and content planning pipeline."
---

## 1) Purpose

Transform first-party performance data (GA4, GSC, logs) into structured entity-level signals that inform content prioritization, cannibalization detection, and opportunity discovery.

This skill defines:
- **Connectors**: GA4 Data API, GSC Search Analytics API, access log parser (Apache/Nginx).
- **Normalizer**: unified schema for `date,url,query,clicks,impressions,avg_position,sessions,user_agent`.
- **Entity mapper**: query→entity association (lemmatization, alias lists, intent).
- **Signals**: decay slopes, cannibalization clusters, opportunity scoring.

You use it to:
- detect entity-level cannibalization & decay
- map real user demand to knowledge-graph nodes
- enrich clusters with click & impression signals
- feed Forecaster and Monitoring

## 2) Novelty rationale

Most tools stop at keywords/URLs; this maps **behavior→entities**. Unified, deterministic, offline-first normalization with cross-signal scoring.

## 3) Trigger conditions

**Use when** site has GA4/GSC/logs; **Avoid** brand-new sites w/o data.

## 4) Prerequisites

GA4/GSC credentials, server logs, TAA knowledge_graph, Python 3.11+.

Recommended: *Entity Reconciler*, *Impact Forecaster*.

## 5) Sources (TOP_25)

- Google Analytics Data API v1
- Google Search Console API
- W3C Extended/Combined Log Format
- HTTP/1.1 semantics (RFC 9110)
- Decay methodologies (industry references)

## 6) Conceptual model

```
[GA4] [GSC] [Logs] → Normalize → Join → Map Queries→Entities → Compute Signals → Export
```

## 7) Procedure

**Step 0 — Extract**: export daily GA4, GSC, rotate logs → `/data/raw/{source}_YYYYMMDD.csv`

**Step 1 — Normalize**: timezone align; lowercasing; bot-filter; schema fields enforced.

**Step 2 — Join**: join GA4/GSC by (url,date); augment with logs (404/5xx, crawl hits).

**Step 3 — Entity Mapping**: lemmatize; alias match; intent tag; confidence≥0.85; unmapped→`/out/ingest/unmapped_queries.csv`.

**Step 4 — Signals**:
- `ctr = clicks / impressions`
- `decay_slope` via OLS on 8–12w window
- cannibalization = same entity+intent → multiple URLs
- opportunity = impressions × (ctr_gap) × (rank_potential)

**Step 5 — Export**:
- `/out/ingest/entity_metrics.parquet`
- `/out/ingest/cannibalization.json`
- `/out/ingest/decay_report.json`

## 8) Artifacts produced

- `entity_metrics.parquet` — per-entity metrics
- `cannibalization.json` — clusters of overlapping URLs
- `decay_report.json` — slope & confidence
- `unmapped_queries.csv` — backlog for alias expansion

## 9) Templates

**entity_metrics.yaml**
```yaml
columns:
  entity_id: string
  clicks: int
  impressions: int
  ctr: float
  avg_position: float
  decay_slope: float
  urls: list
```

## 10) Anti-patterns

- Summing GA4/GSC sessions without dedupe
- Timezone drift
- Mixing brand & generic intents

## 11) Integration with other skills

- **Impact Forecaster**: uses opportunity/decay
- **Monitoring Agent**: builds deltas
- **Competitive Modeler**: merges clickshare
- **Programmatic Factory**: suppress cannibalized entities
