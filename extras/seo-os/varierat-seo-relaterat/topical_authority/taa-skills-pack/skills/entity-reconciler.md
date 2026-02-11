---
name: "Entity Reconciliation & E-E-A-T Graph"
slug: "entity-reconciler"
version: "1.0.0"
tags: ["#entities", "#wikidata", "#schemaorg", "#eeat", "#seo", "#trust"]
summary: "Align knowledge graph entities with authoritative external datasets (Wikidata, Schema.org), unify aliases, and build an E-E-A-T graph connecting authors, organizations, and citations."
---

## 1) Purpose

Create canonical, verifiable identities for every entity in the knowledge graph and link them to external knowledge sources and trustworthy author/organization graphs.

This skill defines:
- **Entity reconciliation** with Wikidata and Schema.org.
- **Alias resolution** (merge dupes + redirects).
- **E-E-A-T graph** (authors ↔ orgs ↔ citations).
- **Provenance manifest** (source/timestamp/confidence).

You use it to: validate/unify entities, emit sameAs, strengthen author/brand authority.

## 2) Novelty rationale

Entities as linked data nodes (not keywords), provenance-first and E-E-A-T aware.

## 3) Trigger conditions

**Use** graph hardening, schema prep; **Avoid** unstable/transient topics.

## 4) Prerequisites

knowledge_graph.json, optional Wikidata access, alias seeds (`/lang/{code}/aliases.yaml`).

## 5) Sources (TOP_25)

- Wikidata SPARQL
- Schema.org
- Helpful Content/E-E-A-T
- CrossRef/OpenAlex
- ISO 27701 (provenance)

## 6) Conceptual model

```
Graph → Alias Normalize → External Reconcile → sameAs+Provenance → Author/Org/Citations → Export
```

## 7) Procedure

1. Load graph nodes.
2. Alias normalize (≥0.90 sim; update edges).
3. External reconcile (confidence≥0.85; store IDs + descriptions; log ambiguity).
4. Author/Org graph: parse briefs/schema → link authors to entities & org.
5. Citation harvest: outbound refs, DOIs, publishers → link to entities.
6. Export: `reconciled_entities.json`, `author_org_graph.json`, `alias_index.tsv`, `provenance_manifest.json`.

## 8) Artifacts produced

- `reconciled_entities.json` — unified nodes w/ sameAs
- `author_org_graph.json` — E-E-A-T network
- `alias_index.tsv` — merged variants
- `provenance_manifest.json` — source/method/confidence

## 9) Templates

**aliases.yaml**
```yaml
aliases:
  "AI": ["artificial intelligence", "machine learning"]
  "EV": ["electric vehicle", "elbil"]
  "SEO": ["search engine optimization"]
```

## 10) Anti-patterns

- sameAs utan tröskel
- övermerge via substring
- saknad provenance

## 11) Integration

- **Schema Compiler**: precise JSON-LD sameAs
- **Quality Harness**: factual consistency
- **Competitive Modeler**: normalized sets
- **Impact Forecaster**: de-duplicate demand
