# Synapse Engine — Model Spec Pack (v1)

**Date:** 2026-02-05  
**Purpose:** A *portable*, *explainable* SEO analysis model that can ingest almost any SEO-relevant data (SERP, Ads, GSC, crawl, content) and output:
- a **synapse graph** (queries ↔ queries, with evidence + strength)
- **clusters** (topic communities)
- **intent + perspective axes** (so non-SEO writers can “see” wrong intent without reading)
- **anchor-safety** (warn when anchor/query belongs to a different cluster than the target page)

This pack is designed to be handed to an LLM agent (Gemini/Claude/etc.) **as operating doctrine + executable contracts**.

---

## What you get

### 1) Concept & architecture docs
- `01_docs/01_concept-model.md` — neutral “how this approximates Google”
- `01_docs/02_models-overview.md` — models M0–M9 (minimal but universal)
- `01_docs/03_visual-rules.md` — how to make maps that read “at a glance”
- `01_docs/04_anchor-safety.md` — how to prevent wrong-intent anchors
- `00_existing/seo-model-architecture.md` — Claude’s architecture note (kept as reference)

### 2) Executable specs (YAML)
- `02_specs/intent_model.yaml`
- `02_specs/perspective_model.yaml`
- `02_specs/evidence_model.yaml`
- `02_specs/scoring_model.yaml`
- `02_specs/clustering_model.yaml`
- `02_specs/visual_model.yaml`
- `02_specs/normalization_model.yaml`
- `02_specs/pack.template.yaml` — how to create a vertical/market pack

### 3) JSON Schemas (strict outputs)
- `03_schemas/IntentJudgeOutput.schema.json`
- `03_schemas/SynapseCard.schema.json`
- `03_schemas/RelatedQueriesOutput.schema.json`
- `03_schemas/GraphArtifact.schema.json`

### 4) Prompt templates (strict JSON)
- `04_prompts/seed_decomposer.md`
- `04_prompts/intent_judge.md`
- `04_prompts/entity_resolver.md`
- `04_prompts/candidate_expander.md`
- `04_prompts/synapse_explainer.md`
- `04_prompts/cluster_labeler.md`

### 5) Visual demo (data-driven)
- `05_visual/synapse-map-viewer.html` — loads a `GraphArtifact` JSON and renders intent×perspective map
- `artifacts_sample/graph.privatlan.sample.json` — sample data to test viewer
- `00_existing/cluster-map-demo.html` — original static demo (kept)

### 6) Minimal reference implementation (optional)
- `06_reference/pipeline_pseudocode.md` — end-to-end steps (no secrets)
- `06_reference/types.ts` — TypeScript types mirroring schemas (handy for plugin dev)
- `06_reference/scoring_reference.py` — scoring + MMR selection (minimal)

---

## How an agent should use this pack

1) Read docs in `01_docs/` (Concept → Models → Visual → Anchor Safety)
2) Treat YAML in `02_specs/` as the **source of truth** for rules & weights
3) Enforce JSON output using schemas in `03_schemas/`
4) Run prompts from `04_prompts/` ONLY in strict JSON mode
5) Output artifacts:
   - `GraphArtifact.json`
   - `RelatedQueriesOutput.json`
   - (optional) `AnchorSafetyReport.json`
6) Render map with `05_visual/synapse-map-viewer.html`

---

## Minimal runtime inputs (to handle “any data”)

The system supports partial-data runs. It always tags **provenance**.

### Required
- `seed_phrase`, `language`, `market`

### Strongly recommended (any one)
- SERP snapshot (top URLs + features + PAA/related)
- Ads keyword ideas
- GSC queries (if site context exists)

### Optional but powerful
- Crawl content (titles/H1/sections for target URLs)
- Entity KB (KG/Wikidata or internal)
- Embeddings (local sentence-transformers)

---

## Existing reference artifacts

- Static demo HTML: `00_existing/cluster-map-demo.html`
- Architecture note: `00_existing/seo-model-architecture.md`

