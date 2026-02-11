# Prompt: Cluster Labeler (M8) — STRICT JSON

## System
Output ONLY JSON.

## Task
Given a cluster with its top phrases, dominant intent distribution, and dominant perspective,
output a short, human-friendly label plus hub_entities.

## Output schema
{
  "cluster_id":"string",
  "label":"string",
  "dominant_intent":"informational|howto|commercial|transactional|navigational|local|freshness",
  "dominant_perspective":"provider|seeker|advisor|regulator|neutral",
  "hub_entities":["string"]
}
