# Models Overview (M0–M9)

The system is a set of small decision engines. Some can be deterministic, some are best as LLM judges, some are pure math.

## Core models (minimum viable)

### M0 — Normalization
Canonicalize spelling/variants, language variants, tokenization rules, and “stop” patterns.

### M1 — Seed Decomposer
Turn the seed query into:
- entities (+ roles)
- intent hypotheses + SERP prediction
- perspective
- facets to expand (10–20)

### M2 — Entity Resolver
Entity extraction + typing + reconciliation (KG if available; otherwise stable hash IDs).

### M3 — Candidate Generator
Build a candidate pool (200–2000):
- Tier 1: Ads ideas / GSC queries
- Tier 2: SERP-derived expansions (PAA/related/autocomplete)
- Tier 3: LLM expansion via facets + synapse pathways (marked `llm_only` until validated)

### M4 — Intent Judge
Classify:
- dominant interpretation
- common/minor interpretations
- intent mix
- confidence + evidence used  
(Prefer 2-phase: rules → LLM judge with SERP snapshot.)

### M5 — Perspective Judge
Assign perspective (provider/seeker/advisor/regulator/neutral) with confidence.
This can be integrated into M4, but is separated here for clarity & tuning per vertical.

### M6 — Synapse Builder
For seed↔candidate (and within clusters where needed) output:
- synapse types
- strength
- evidence card (URLs/features/entities) + provenance

### M7 — Scoring + Selection (Top-50)
Compute `relevance_score(seed, candidate)` from:
- entity overlap
- SERP overlap (if available)
- embedding similarity
- intent distance
- perspective distance
Then select top 50 with **MMR** (relevance + diversity constraints).

### M8 — Clustering + Topic Labels
Cluster the selected set (3–8 clusters typical) using composite distance.
Label each cluster via dominant entities + intent + perspective.

### M9 — Visual Renderer
Render a 2D map that is readable without reading:
- x-axis: intent spectrum (info→transactional)
- y-axis: perspective spectrum (seeker→provider)
- color: cluster
- size: relevance or volume
- opacity/border: confidence + provenance
- edges: only above a strength threshold

---

## Optional models (for “any SEO analysis”)

### O1 — Target Page Profile Model
Infer intent/perspective of a target URL from:
title/H1/CTA, content, schema, internal links, SERP result type.
Produces a `TargetIntentProfile`.

### O2 — Anchor Safety Model
Given target profile + candidate anchor phrase:
compute distance; output PASS/WARN/FAIL + why (non-SEO friendly).

### O3 — Topical Authority Coverage Model
Given site pages + clusters:
identify coverage gaps, cannibalization risk, internal link graph recommendations.

### O4 — Calibration Model
Validate predicted synapse strengths against external data (SERP overlap etc.).
Adjust weights over time; store vertical-specific tuning.
