# Prompt: Entity Resolver (M2) — STRICT JSON

## System
Output ONLY JSON.

## Task
Given a phrase, extract entities and type them. If KG IDs are unavailable, create stable IDs as:
`e.<type>.<slug>` where slug is a normalized ascii/slug of the canonical label.

## Output schema
{
  "phrase": "string",
  "entities": [
    {"id":"string","surface":"string","canonical":"string","type":"topic|brand|product|regulation|metric|action|attribute|amount","kg_id":null,"role":"subject|object|modifier|action","confidence":0.0}
  ],
  "evidence_used": ["string"],
  "notes": "string"
}
