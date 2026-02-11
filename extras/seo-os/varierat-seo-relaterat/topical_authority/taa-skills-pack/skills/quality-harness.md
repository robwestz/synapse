---
name: "Content Quality & Factuality Harness"
slug: "quality-harness"
version: "1.0.0"
tags: ["#quality", "#factuality", "#citations", "#thin-content", "#evaluation"]
summary: "Evaluate content for factual accuracy, depth, and authoritativeness. Detect thin or redundant pages and verify claims using retrieval-augmented grounding."
---

## 1) Purpose

Ensure content credibility, completeness, and uniqueness. Evaluate topical depth, factual grounding, and redundancy.

This skill defines:
- **Claim extraction & citation tracing**
- **Thin-content detection** (entity density & overlap)
- **RAG verification** (optional online)
- **E-E-A-T scoring** (explainable)

You use it to: flag shallow/duplicate, verify facts, audit author expertise.

## 2) Novelty rationale

Measures semantic completeness & verifiable factuality, not wordcount.

## 3) Trigger conditions

**Use** audits/republishing/QA; **Avoid** pure opinion pieces.

## 4) Prerequisites

briefs/*.md or HTML; reconciled entities; optional corpus.

## 5) Sources

- HCU/E-E-A-T guidelines
- ClaimReview
- Wikipedia dumps

## 6) Conceptual model

```
Pages → Claims+Entities → Grounding → Scores → Quality Report
```

## 7) Procedure

1. Load content; split sentences.
2. Extract entities & claims (S-P-O triples).
3. Ground verification (offline TF-IDF/embeddings; optional online).
4. Compute: entity coverage, factuality rate, redundancy index, E-E-A-T subscores.
5. Export: `quality_report.csv`, `fact_check.json`, `thin_content_list.md`.

## 8) Artifacts produced

- `quality_report.csv`
- `fact_check.json`
- `thin_content_list.md`

## 9) Templates

**quality_report.csv**
```csv
page,entity_coverage,factuality_score,eeat_score,thin_flag
horapparater-pris,0.92,0.88,0.91,false
horapparater-bidrag,0.74,0.65,0.70,true
```

## 10) Anti-patterns

- Wordcount as proxy
- Untrusted web sources
- Ignoring author metadata

## 11) Integration

- **Monitoring Agent**: catch regressions
- **Programmatic Factory**: QA gate
- **Delivery DevOps**: CI gate
- **Impact Forecaster**: adjust projections
