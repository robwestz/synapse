# Prompt: Synapse Explainer (M6) — STRICT JSON

## System
Return ONLY valid JSON matching `SynapseCard.schema.json`.

## Task
Given two queries (from_id/to_id), their intent+perspective labels, and available evidence (shared URLs/entities/features),
produce:
- types[] (choose 1..3)
- strength (0..1)
- bridge_statement (1 sentence, non-SEO friendly)
- evidence[] entries (each with source, kind, summary, confidence)

## Rules
- If evidence is only LLM-inferred, cap confidence <= 0.55
- Strength must reflect evidence quality (SERP overlap outranks lexical similarity)

