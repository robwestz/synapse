---
name: "Render Crawler & Site Audit"
slug: "render-crawler"
version: "1.0.0"
tags: ["#crawler", "#rendering", "#hreflang", "#canonical", "#robots", "#audit"]
summary: "Headless crawler that renders, audits, and maps site structure, producing crawl budget simulations, indexability reports, and schema inventories."
---

## 1) Purpose

Crawl+render pages with JS execution; audit indexability, canonical signals, hreflang, and structured data. Output feeds graph & linking modules.

This skill defines:
- **Fetcher** (sitemaps+discovery+robots)
- **Renderer** (headless Chromium)
- **Auditor** (canonical/hreflang/meta/schema)
- **Budget simulator** (depth/cost curves)

You use it to: detect render blockers, duplicates, hreflang/canonical issues, schema gaps.

## 2) Novelty rationale

JS-aware, SPA-tolerant, graph-integrated; offline replay via cached HTML snapshots.

## 3) Trigger conditions

**Use** audits, pre-launch checks, periodic tech reviews; **Avoid** unbounded huge sites.

## 4) Prerequisites

Playwright/Chromium, seed list/sitemap, Python libs (playwright, bs4, pandas).

## 5) Sources

- Google JS SEO
- sitemap.org
- robots.txt
- RFC 9110
- JSON-LD/Schema.org

## 6) Conceptual model

```
Seeds → Fetch+Render → Extract (meta/canon/hreflang/schema) → Indexability+Cost → Export
```

## 7) Procedure

1. Init seeds; honor robots.
2. Render w/ 5s timeout; save HTML cache + network summary.
3. Extract: `<title>`, meta robots, canonical, hreflang, JSON-LD.
4. Compute: render_time_ms, dom_nodes_count, indexable, canonical_status, schema_types.
5. Budget sim: depth vs cost, crawl waste%.
6. Export: `/out/crawl/url_index.csv`, `audit_issues.md`, `schema_inventory.json`, `budget_simulation.csv`.

## 8) Artifacts produced

- `url_index.csv` — per URL status & metrics
- `audit_issues.md` — grouped issues
- `schema_inventory.json` — JSON-LD inventory
- `budget_simulation.csv` — crawl economics

## 9) Templates

**audit_issues.md**
```markdown
# Crawl Audit Summary
Total URLs: 2,345
Indexable: 2,112
Blocked by robots: 87
Canonical mismatch: 45
Missing hreflang: 66
Render timeout (>5 s): 35
```

## 10) Anti-patterns

- Ignoring robots
- Rendering faceted/infinite URLs
- Deleting cache → non-determinism

## 11) Integration

- **Link Graph Analytics**: URL graph
- **Schema Compiler**: validate JSON-LD
- **Monitoring Agent**: change detection
- **Impact Forecaster**: crawl ROI inputs
