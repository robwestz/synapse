# Synapse Engine Prototype + API Module

This folder is a **working, offline-friendly** reference implementation of the `synapse-engine-spec-v1` pack
**plus** a first-class *API connectors module* (DataForSEO, Ahrefs, Firecrawl) and a tiny local UI.

It can run without external APIs (SERP/Ads/GSC/LLM) by using:
- rule-based intent + perspective detection from the YAML specs
- TF‑IDF cosine similarity as an embedding proxy
- hierarchical clustering on a composite distance matrix

Outputs are validated against the JSON Schemas:
- `GraphArtifact.schema.json`
- `RelatedQueriesOutput.schema.json`

## Run (offline demo)

```bash
python run_demo.py
```

Then open:
- `out/viewer.html` (self-contained)

## Run (local UI + API connectors)

1) Install deps

```bash
pip install -r requirements.txt
```

2) Start the server

```bash
uvicorn server:app --reload --port 8080
```

3) Open the UI

- http://localhost:8080

Paste your keys (optional) and run a seed.

### Supported providers (v0.2)

- **DataForSEO** (SERP snapshot + keyword suggestions + related keywords)
- **Ahrefs API v3** (keywords matching terms)
- **Firecrawl** (client included; not yet wired into candidate generation)

Nothing is mandatory: if you don't provide any keys, the pipeline falls back to deterministic offline candidates.

## Replace stubs with more real data

Swap these modules:
- `synapse_engine/candidates.py` -> Ads API / GSC / SERP candidates
- `synapse_engine/intent.py` + `perspective.py` -> LLM Judge prompt (M4/M5)
- `synapse_engine/entities.py` -> KG lookup or Wikidata
- `synapse_engine/synapses.py` -> LLM Synapse Explainer prompt (M6)

### Where the API module plugs in

- `synapse_engine/secrets.py` – load/merge secrets from env + local file + UI payload
- `synapse_engine/providers/*` – provider clients
- `synapse_engine/runtime.py` – budgets + provider registry
- `synapse_engine/pipeline.py` – optional SERP refinement + provenance-aware confidence caps

