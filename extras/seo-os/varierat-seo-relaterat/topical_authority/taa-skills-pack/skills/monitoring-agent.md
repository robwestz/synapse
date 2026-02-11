---
name: "Continuous Monitoring & Diff Agent"
slug: "monitoring-agent"
version: "1.0.0"
tags: ["#monitoring", "#diffs", "#alerts", "#regression", "#automation"]
summary: "Automated watcher that compares entity metrics, crawl data, and schema between runs to detect regressions, orphan pages, and ranking losses, producing diff reports and alerts."
---

## 1) Purpose

Continuously track changes in entity performance, crawl structure, and schema coverage. Detect regressions early and surface actionable diffs.

This skill defines:
- **Artifact diffs** (JSON/CSV/MD)
- **Regression detection** (clicks, coverage, links)
- **Alerts** (JSON + webhooks)
- **Run logs** (deterministic audit)

You use it to: see what changed, catch orphans/schema loss, alert teams.

## 2) Novelty rationale

Tracks semantic integrity (entities/clusters/links), not just URLs.

## 3) Trigger conditions

**Use** weekly/monthly builds, migrations; **Avoid** first run.

## 4) Prerequisites

`/out/run_prev`, `/out/run_curr`; optional GSC/GA4.

## 5) Sources

- Myers diff
- GSC API
- JSON Schema Draft

## 6) Conceptual model

```
Prev ↔ Curr → Structural+Metric Diffs → Classify → Alerts
```

## 7) Procedure

1. Load manifests; enumerate comparable files.
2. Diff JSON/YAML with structural diff; Markdown line diff.
3. Classify: ENTITY_LOSS, SCHEMA_REMOVED, ORPHAN_PAGE, TRAFFIC_DROP.
4. Aggregate alerts (multi-signal = higher severity).
5. Export: `diff_report.md`, `alerts.json`, `run_log/{timestamp}.log`.

## 8) Artifacts produced

- `diff_report.md` — human summary
- `alerts.json` — machine payload
- `run_log/` — audit logs

## 9) Templates

**alerts.json**
```json
[
  {"entity":"hörapparater","type":"TRAFFIC_DROP","severity":"high","old_value":1280,"new_value":880,"change_pct":-31.2,"detected_at":"2025-12-25T10:00:00Z"}
]
```

**diff_report.md**
```markdown
# TAA Diff Report — 2025-12-25
- Entities added: 12
- Entities removed: 3
- Orphan pages: 1
- High-severity alerts: 2
```

## 10) Anti-patterns

- Comparing incomplete builds
- Timestamp misalignment
- Alert spam (no grouping)

## 11) Integration

- **Impact Forecaster**: calibrate models
- **Quality Harness**: content cause analysis
- **Delivery DevOps**: rollback/redo
- **Schema Compiler**: revalidate
