# Synapse Engine — SEO Intelligence Framework

Maps search queries onto a 2D **Intent x Perspective** coordinate system. Generates interactive synapse maps where clusters, distances, and connections reveal SEO opportunities that no table can show.

## Quickstart (4 steps)

```bash
# 1. Clone & enter
cd synapse-engine

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r apps/api/requirements.txt

# 4. Run demo (no API keys needed)
cd apps/prototype
python run_demo.py
# Open out/viewer.html in your browser
```

## Run the API server

```bash
cd apps/api
cp .env.example synapse_engine/.env    # Add your API keys
uvicorn server:app --reload --port 8080
```

- Swagger: http://localhost:8080/docs
- POST http://localhost:8080/api/run with JSON body:

```json
{
  "seed_phrase": "privatlån upp till 800 000",
  "language": "sv",
  "market": "SE",
  "target": 30
}
```

## Architecture

```
Seed phrase
  |
  M0  Normalize ── normalization.py
  M3  Candidates ── candidates.py (DataForSEO + Ahrefs + templates)
  M4  Intent ── intent.py (7 types: informational → transactional)
  M5  Perspective ── perspective.py (5 types: seeker → provider)
  M7  Scoring ── scoring.py (TF-IDF + MMR selection)
  M8  Clustering ── clustering.py (hierarchical, composite distance)
  M6  Synapses ── synapses.py (edges with evidence cards)
  M9  Visual ── visual.py (2D positioning + anchor safety)
  |
  Output: GraphArtifact.json + viewer.html
```

Orchestrator: `apps/api/synapse_engine/pipeline.py` (~290 lines).

## Structure

```
spec/synapse-engine-spec-v1/   # YAML specs, JSON schemas, prompt templates
apps/prototype/                # Offline demo (no API keys needed)
apps/api/                      # FastAPI server + synapse_engine package
extras/seo-os/                 # 20 intelligence modes (reference)
assets/                        # HTML viewers + architecture docs
```

## API Keys (optional)

Without keys the pipeline runs in offline mode (templates + TF-IDF). With keys:

| Key | Source | Purpose |
|-----|--------|---------|
| `DATAFORSEO_LOGIN/PASSWORD` | dataforseo.com | SERP data + keyword suggestions |
| `AHREFS_API_KEY` | ahrefs.com | Keyword matching terms |
| `FIRECRAWL_API_KEY` | firecrawl.dev | Web scraping (optional) |
| `ANTHROPIC_API_KEY` | console.anthropic.com | LLM integration (Phase 1) |

See `apps/api/.env.example` for full template.

## Tests

```bash
cd apps/api
pytest tests/ -v
```

## What makes this different

1. **Perspective as first-class dimension** — "privatlån 800 000" (provider) vs "betala av lån 800 000" (seeker) cluster separately
2. **Visual-first output** — The map IS the deliverable
3. **Explainable edges** — Every connection has a bridge statement with evidence
4. **Provenance-aware confidence** — llm_inferred capped at 0.55, SERP-backed up to 0.90
5. **Anchor safety warnings** — Flags queries dangerous as anchor text
6. **Offline-capable** — Full pipeline runs without any API keys
# synapse
