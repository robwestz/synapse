---
name: "Structured Data Compiler & Validator"
slug: "schema-compiler"
version: "1.0.0"
tags: ["#schema", "#json-ld", "#structured-data", "#validation"]
summary: "Generate, validate, and optimize JSON-LD structured data bundles for all pages and entities, ensuring schema compliance and SERP feature readiness."
---

## 1) Purpose

Automate Schema.org markup from entities & briefs; validate structure and simulate SERP feature readiness.

This skill defines:
- **JSON-LD compiler**
- **Validator harness**
- **Feature scoring**
- **Schema diffing**

You use it to: maintain coverage, debug rich results, plan feature wins.

## 2) Novelty rationale

Entity-driven synthesis + validation, not static snippets.

## 3) Trigger conditions

**Use** publish/update/audit; **Avoid** non-indexable pages.

## 4) Prerequisites

reconciled_entities.json, briefs/*.md.

## 5) Sources

- Schema.org
- Google Rich Results Test
- JSON-LD 1.1

## 6) Conceptual model

```
Entities+Briefs → Compile → Validate → Score → Export JSON-LD
```

## 7) Procedure

1. Generate schema blocks from types (FAQ/Product/HowTo/etc.).
2. Validate via jsonschema.
3. Feature scoring by completeness/eligibility.
4. Export: `/out/schema/jsonld/*.json`, `validation_report.md`, `feature_scores.csv`.

## 8) Artifacts produced

- `jsonld/*.json`
- `validation_report.md`
- `feature_scores.csv`

## 9) Templates

**validation_report.md**
```markdown
# Schema Validation Summary
Valid JSON-LD: 87/90
Warnings: 3
Errors: 0
Top Missing Fields:
- AggregateRating (3)
- offers.price (2)
```

## 10) Anti-patterns

- Hardcoded snippets
- Conflicting @types
- Missing @context/@id

## 11) Integration

- **Monitoring Agent**: schema diffs
- **Programmatic Factory**: injection
- **Delivery DevOps**: pre-publish gate
