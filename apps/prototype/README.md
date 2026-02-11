# Synapse Engine Prototype

This folder is a **working, offline-friendly** reference implementation of the `synapse-engine-spec-v1` pack.

It runs without external APIs (SERP/Ads/GSC/LLM) by using:
- rule-based intent + perspective detection from the YAML specs
- TF‑IDF cosine similarity as an embedding proxy
- hierarchical clustering on a composite distance matrix

Outputs are validated against the JSON Schemas:
- `GraphArtifact.schema.json`
- `RelatedQueriesOutput.schema.json`

## Run

```bash
python run_demo.py
```

Then open:
- `out/viewer.html` (self-contained)

## Replace stubs with real data

Swap these modules:
- `synapse_engine/candidates.py` -> Ads API / GSC / SERP candidates
- `synapse_engine/intent.py` + `perspective.py` -> LLM Judge prompt (M4/M5)
- `synapse_engine/entities.py` -> KG lookup or Wikidata
- `synapse_engine/synapses.py` -> LLM Synapse Explainer prompt (M6)

