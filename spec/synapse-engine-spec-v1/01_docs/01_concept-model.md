# Concept Model — Neutral “Google-like” Approximation

This spec does **not** claim to know Google’s internal weights. It defines a *measurable proxy* model that tends to match what Google *exposes* (SERP layouts, result types, query refinements, related searches).

## Core objects

### 1) Entity (E)
A “thing” (named entity or concept) that can be referred to consistently.

- **Examples:** “SBAB” (brand), “privatlån” (product concept), “effektiv ränta” (metric), “konsumentkreditlagen” (regulation).

### 2) Query (Q)
A search phrase interpreted as:
- entities + roles (subject/object/modifier)
- intent (what the user is trying to accomplish)
- perspective (whose viewpoint is implied)
- expected SERP mix (layout / result types)

### 3) Synapse (S)
An *edge* between two queries:
- **type(s):** shared-entity, facet-transform, task-chain, comparative, problem→solution, SERP-overlap, etc.
- **strength:** 0..1
- **evidence:** what supports this edge (SERP overlap, shared entities, PAA, Ads ideas, GSC, embeddings)
- **provenance:** serp|ads|gsc|crawl|llm_only

### 4) Cluster (C)
A community of queries that:
- share entities/facets
- have similar intent + perspective
- produce similar SERP layouts

Clusters must be *visually separable* (so a non-SEO person can infer “wrong cluster” without reading labels).

---

## Two-layer view (practical)

### Layer A — Entity Graph (EG)
Nodes: entities  
Edges: relations (is-a, part-of, requires, compared-with, etc.)

### Layer B — Query Graph (QG)
Nodes: queries  
Edges: synapses (query↔query).  
Cluster = community in QG.

QG can be built even if EG is incomplete. EG improves stability and explainability.

---

## Why “Perspective” is first-class

**Perspective** = “who is speaking / what role is implied in the query”.

- provider: seller/lender/operator (“privatlån upp till 800 000”, “ansök online”)
- seeker: the user has the problem (“betala av lån”, “jag har …”)
- advisor: comparison/review voice (“bästa”, “jämför”, “recension”)
- regulator: rules/compliance (“lag”, “krav”, “Finansinspektionen”)
- neutral: encyclopedic/definition

Perspective is a *primary reason* that two phrases can share entities but still produce totally different SERPs.

---

## “Google-like” signals we can measure

1) **SERP features**: ads, local pack, PAA, videos, shopping, top stories
2) **Result-type mix**: banks vs comparison sites vs editorial vs forums vs regulators
3) **URL overlap**: Jaccard overlap on top-N URLs (strong proxy for same interpretation)
4) **Query refinements**: related searches + PAA + autocomplete
5) **Entity overlap**: entities extracted from snippets/title/schema/corpus
6) **Embeddings**: semantic proximity as a backstop (not a replacement)

---

## What the map must convey (human factors)

A map is successful if it makes this intuitive:

> “These two phrases look similar, but they are far apart (different intent/perspective).  
> Therefore: wrong anchor / wrong content / different URL.”

That’s why we encode **intent × perspective** as the primary axes.
