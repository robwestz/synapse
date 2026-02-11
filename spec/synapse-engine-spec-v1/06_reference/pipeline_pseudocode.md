# Minimal Pipeline (Reference)

This is intentionally minimal and tool-agnostic. Replace data sources as needed.

## Inputs
- seed_phrase, language, market
- optional: serp_snapshot, ads_ideas, gsc_queries, embeddings, crawl_entities

## Steps

1) Normalize seed (M0)
2) Seed Decompose (M1)
3) Candidate pool (M3)
   - collect tier1/tier2 sources
   - add tier3 LLM candidates (tag llm_only)
   - dedupe
4) Intent+Perspective for candidates (M4+M5)
   - rule pass (cheap)
   - LLM judge for selected_50 (or for all, budget permitting)
5) Score all candidates vs seed (M7)
   - compute components
6) Select top 50 with MMR (M7)
7) Build synapses (M6)
   - seed↔node for all selected
   - optional: intra-cluster edges
8) Cluster (M8)
9) Assign coordinates (intent_x + perspective_y) (M9 input)
10) Emit artifacts:
    - RelatedQueriesOutput.json
    - GraphArtifact.json

## Notes
- Every field must carry provenance and confidence.
- If SERP is unavailable, cap confidence (do not pretend).
