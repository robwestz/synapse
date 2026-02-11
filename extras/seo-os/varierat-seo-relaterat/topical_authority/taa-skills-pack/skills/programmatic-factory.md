---
name: "Programmatic SEO Factory"
slug: "programmatic-factory"
version: "1.0.0"
tags: ["#automation", "#programmatic-seo", "#templates", "#scaling"]
summary: "Generate large-scale parametric SEO pages from entity templates with uniqueness guards, structured schema, and auto-deindex rules."
---

## 1) Purpose

Generate scalable long-tail content safely with semantic uniqueness and schema completeness.

This skill defines:
- **Parameterized templates** (Jinja-like)
- **Uniqueness guard** (semantic similarity)
- **Auto-noindex rules**
- **Schema injection hooks**

You use it to: launch location/SKU/comparison collections at scale.

## 2) Novelty rationale

Programmatic SEO with semantic uniqueness (not random filler).

## 3) Trigger conditions

**Use** category/location/variant pages; **Avoid** creative/opinion content.

## 4) Prerequisites

topic_clusters.json, `/templates/*.jinja`.

## 5) Sources

- Duplicate/canonical guidelines
- Schema.org

## 6) Conceptual model

```
Templates → Render → Uniqueness QA → Schema Injection → Export
```

## 7) Procedure

1. Load templates; validate placeholders.
2. Render pages per entity variant.
3. Similarity check; if not unique → flag/noindex.
4. Inject JSON-LD via Schema Compiler.
5. Export: `pages/*.html`, `noindex_list.txt`, `manifest.json`.

## 8) Artifacts produced

- `pages/*.html`
- `noindex_list.txt`
- `manifest.json`

## 9) Templates

**page_template.jinja**
```jinja
<h1>{{ entity.label }} – {{ modifier }}</h1>
<p>{{ entity.description }}</p>
{% for item in highlights %}<h2>{{ item.title }}</h2><p>{{ item.text }}</p>{% endfor %}
```

## 10) Anti-patterns

- Random variation
- No QA
- Blanket noindex by mistake

## 11) Integration

- **Quality Harness**: factuality/uniqueness check
- **Schema Compiler**: JSON-LD injection
- **Delivery DevOps**: deployment
- **Monitoring Agent**: template performance
