# Prompt: Candidate Expander (M3 Tier-3) — STRICT JSON

## System
Output ONLY JSON.

## Task
Generate candidate queries by traversing:
- facets from Seed Decomposer
- synapse pathways (taxonomic, attribute, intent-shift, procedural, association, problem/solution, comparative, contextual bridge)

All output candidates MUST be tagged with:
- pathway_id (1..8)
- provenance="llm_inferred"
- rationale (1 sentence)

## Output schema
{
  "seed_phrase":"string",
  "candidates":[
    {"phrase":"string","pathway_id":1,"provenance":"llm_inferred","rationale":"string"}
  ]
}
