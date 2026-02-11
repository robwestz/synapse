# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What This Is

Synapse Engine is an SEO intelligence framework that maps search queries onto a 2D **Intent x Perspective** coordinate system. It generates interactive visual maps ("synapse maps") where non-experts can see which queries are close to each other and which are far apart — without understanding search intent theory.

The core insight: two phrases can share the same words but live in completely different SERP realities because of **perspective** (provider vs seeker vs advisor vs regulator). No other SEO tool treats perspective as a first-class axis.

---

## Running the System

### Prototype (offline, no API keys needed)

```bash
cd synapse-engine/apps/prototype
python -m venv .venv && .venv\Scripts\activate
pip install PyYAML jsonschema numpy scikit-learn
python run_demo.py
```

Output: `out/GraphArtifact.json`, `out/RelatedQueriesOutput.json`, `out/viewer.html`
Open `out/viewer.html` in a browser to see the synapse map.

### API Server (with provider integrations)

```bash
cd synapse-engine/apps/api
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# Configure keys (see Secrets section below)
uvicorn server:app --reload --port 8080
```

- UI: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`
- POST `http://localhost:8080/api/run` with JSON body

### Viewer Only (static HTML)

Open any of these directly in a browser:
- `spec/synapse-engine-spec-v1/05_visual/synapse-map-viewer.html`
- `assets/viewer.html`
- `assets/cluster-map-demo.html`

---

## Secrets & API Keys

Keys are resolved in priority order: **request payload > persisted file > env vars**.

Persisted location: `~/.synapse_engine/secrets.json`

Required env vars for full functionality (in `apps/api/.env`):
```
DATAFORSEO_LOGIN=       # SERP data + keyword suggestions
DATAFORSEO_PASSWORD=
AHREFS_API_KEY=         # Keyword matching terms
FIRECRAWL_API_KEY=      # Web scraping (optional)
```

The system degrades gracefully: without any keys it falls back to template-based candidate generation with TF-IDF embeddings.

---

## Architecture: Pipeline Stages (M0-M9)

```
Seed phrase ("privatlån upp till 800 000")
  │
  M0  Normalization ─── normalize_phrase() via normalization_model.yaml
  │
  M3  Candidate Generation ─── 200-2000 candidates from:
  │     Tier 1: DataForSEO Labs + Ahrefs v3 (API-backed, high confidence)
  │     Tier 2: SERP PAA + Related Searches (medium confidence)
  │     Tier 3: Template expansion (offline fallback, llm_inferred)
  │
  M4  Intent Classification ─── 7 types: informational→transactional (X-axis)
  M5  Perspective Classification ─── 5 types: seeker→provider (Y-axis)
  │     Both rule-based; confidence capped if no SERP evidence
  │
  M7  Scoring ─── 5 weighted features → MMR selection (top 50)
  │     entity_overlap(25%) + serp_overlap(25%) + embedding_sim(20%)
  │     + intent_compat(15%) + perspective_align(15%)
  │
  M8  Clustering ─── Hierarchical agglomerative (3-8 clusters)
  │     Composite distance: semantic(30%) + intent(25%) + perspective(25%) + entity(20%)
  │
  M6  Synapse Generation ─── Edges with synapse cards (strength, types, evidence)
  │
  M9  Visual Positioning ─── X=intent, Y=perspective + jitter → GraphArtifact.json
```

Entry point: `synapse_engine/pipeline.py:run_pipeline()` — returns `(GraphArtifact, RelatedQueriesOutput)`.

---

## Key Source Files (apps/api/synapse_engine/)

| File | Role |
|------|------|
| `pipeline.py` | Orchestrates M0-M9, returns validated output |
| `candidates.py` | M3: Provider calls + template expansion + dedup |
| `scoring.py` | M7: TF-IDF embeddings, relevance scoring, MMR selection |
| `clustering.py` | M8: Hierarchical clustering with composite distance |
| `intent.py` | M4: Rule-based intent classification (7 types) |
| `perspective.py` | M5: Rule-based perspective classification (5 types) |
| `synapses.py` | M6: Edge generation with synapse cards |
| `visual.py` | M9: 2D positioning + cluster centroids + legend |
| `config.py` | Loads YAML specs into SpecPack objects |
| `runtime.py` | Budget controls + provider registry |
| `secrets.py` | API key management (env + persisted + request) |
| `serp.py` | SERP snapshot fetching + Jaccard overlap |
| `validators.py` | JSON schema validation of output |
| `providers/dataforseo.py` | DataForSEO Labs API client |
| `providers/ahrefs.py` | Ahrefs v3 API client |
| `providers/firecrawl.py` | Firecrawl web scraping client |
| `providers/registry.py` | Provider factory from secrets |

The `apps/prototype/` directory mirrors these modules but runs fully offline (no provider integrations).

---

## Spec-Driven Design

All models are defined in YAML, not code. The code reads these specs at runtime:

| Spec (in `spec/synapse-engine-spec-v1/02_specs/`) | Controls |
|---|---|
| `intent_model.yaml` | 7 intent types, X-axis positions, signal patterns, distance matrix |
| `perspective_model.yaml` | 5 perspectives, Y-axis positions, signal phrases, distance matrix |
| `scoring_model.yaml` | Feature weights, MMR params (lambda=0.75), thresholds |
| `clustering_model.yaml` | Algorithm config, distance composition, target cluster range |
| `evidence_model.yaml` | Confidence caps per provenance (llm_only=0.55, serp=0.90) |
| `visual_model.yaml` | Node/edge encoding, 8-color cluster palette, layout rules |
| `normalization_model.yaml` | Typo mapping, variant rules |

Output contracts enforced by JSON schemas in `spec/.../03_schemas/`:
- `GraphArtifact.schema.json` — The complete graph (nodes, edges, clusters, legend)
- `RelatedQueriesOutput.schema.json` — Flat ranked list
- `SynapseCard.schema.json` — Edge explanation format
- `IntentJudgeOutput.schema.json` — Intent classification result

LLM prompt templates in `spec/.../04_prompts/` (not yet wired into pipeline):
- `seed_decomposer.md`, `intent_judge.md`, `entity_resolver.md`
- `candidate_expander.md`, `synapse_explainer.md`, `cluster_labeler.md`

---

## The Visual Map

The synapse map viewer (`05_visual/synapse-map-viewer.html`) is a self-contained HTML/SVG file:

- **X-axis**: INFORMATIONAL (left) → TRANSACTIONAL (right)
- **Y-axis**: SEEKER (top) → PROVIDER (bottom)
- **Seed**: Red pulsating circle
- **Nodes**: Colored by cluster, sized by relevance/volume
- **Edges**: Thickness = strength, dashed/solid = type
- **Clusters**: Semi-transparent ellipses with labels
- **Tooltips**: Hover shows phrase, intent, perspective, provenance, bridge statement
- **Anchor safety**: Nodes flagged `wrong_cluster_for_anchor` if too far from seed

The viewer embeds `GraphArtifact.json` directly — portable, no server needed.

---

## Budget Controls

Default budget (tunable per request):
```python
candidate_pool_target = 500     # Total candidates to generate
keyword_suggestions_limit = 400 # DataForSEO keyword_suggestions cap
related_keywords_limit = 250    # DataForSEO related_keywords cap
serp_depth = 10                 # Top N URLs per SERP call
serp_refine_top_n = 30          # Candidates to enrich with SERP overlap
serp_calls_max = 40             # Hard cap for all SERP API calls in one run
```

---

## Extras: SEO Intelligence Modes (reference)

`extras/seo-os/seo-intelligence/` contains 20+ analysis modes for future integration:

| Category | Modes |
|----------|-------|
| Cluster analysis | 1.1 Dominance, 1.2 Long-tail gaps, 1.3 Momentum, 1.4 Entity overlap, 1.5 Intent gaps |
| SERP opportunities | 2.1 PAA hijacking, 2.2 Snippet vulnerability |
| Link intelligence | 3.1 Common linkers, 3.2 Anchor patterns |
| Discovery | 4.1 Hidden traffic, 4.2 Low competition |
| Content strategy | 5.1 Cluster completeness, 5.3 Cannibalization |
| Competitive | 7.1 Competitor profiles, 8.4 Competitive moat |

These are standalone Python modules, not yet integrated into the main pipeline.

---

## Testing Current Functionality

### Quick Smoke Test (offline)
```bash
cd synapse-engine/apps/prototype
python run_demo.py
# Opens out/viewer.html → should show clustered nodes on 2D map
```

### API Smoke Test
```bash
cd synapse-engine/apps/api
uvicorn server:app --port 8080
# Then:
curl -X POST http://localhost:8080/api/run \
  -H "Content-Type: application/json" \
  -d '{"seed_phrase": "privatlån upp till 800 000", "language": "sv", "market": "SE", "target": 30}'
```

### Validate Output Schemas
```python
from synapse_engine.validators import SchemaValidator
from pathlib import Path
sv = SchemaValidator(Path("spec/03_schemas"))
sv.validate(graph, "GraphArtifact.schema.json")
sv.validate(related, "RelatedQueriesOutput.schema.json")
```

### Provider Integration Test
Add keys to `.env`, then POST to `/api/run` with `"secrets": {"dataforseo_login": "...", "dataforseo_password": "..."}`. Check that candidates have `provenance: "ads_api"` and `serp_overlap > 0` for top results.

### Visual Output Test
After any pipeline run, open the generated `viewer.html`. Verify:
1. Seed is centered, red, pulsating
2. Nodes cluster into colored groups
3. X-axis spread reflects intent (informational left, transactional right)
4. Y-axis spread reflects perspective (seeker top, provider bottom)
5. Hover tooltips show synapse card data

---

## What Makes This Different From Every Other SEO Tool

1. **Perspective as first-class dimension** — "privatlån 800 000" (provider) vs "betala av lån 800 000" (seeker) cluster separately despite sharing entities. No other tool does this.

2. **Visual-first output** — The map IS the deliverable. A junior marketer can point at "far apart" nodes without understanding intent theory.

3. **Explainable edges (synapse cards)** — Every connection has a human-readable bridge statement with evidence and provenance. Not a black box.

4. **Provenance-aware confidence** — Every data point tagged with its source. Confidence automatically degrades when evidence is weak (llm_inferred capped at 0.55).

5. **Anchor safety warnings** — Flags queries that look related but are semantically dangerous as anchor text (`wrong_cluster_for_anchor`).

6. **SERP overlap as ground truth** — Uses Jaccard similarity on top URLs as primary signal, not just embeddings. Falls back gracefully when API budget is exhausted.

7. **Offline-capable** — Full pipeline runs without any API keys using templates + TF-IDF + rule-based classification.

