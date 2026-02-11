# Visual Rules — “Readable Without Reading”

## Primary axes

### X-axis: Intent spectrum
Map intents to positions:
- informational: 0.0
- howto: 0.2
- commercial: 0.55
- transactional: 0.85
- navigational: 0.75 (often close to transactional but brand-directed)
- local: 0.65 (varies)
- freshness: 0.35 (overlay/flag)

You can tune per vertical.

### Y-axis: Perspective spectrum
- seeker: 0.15 (top)
- advisor: 0.40
- neutral: 0.55
- regulator: 0.65
- provider: 0.85 (bottom)

Key: **provider vs seeker must be visually far apart**.

---

## Encoding rules

### Cluster zones
Draw soft ellipses behind each cluster (low opacity), labeled.

### Nodes
- size: use volume if available; otherwise relevance_score
- opacity: confidence (low confidence = translucent)
- border style: provenance (solid = ground truth; dashed = llm_only)
- seed: pulse + star marker

### Edges
- show only edges with strength >= threshold (default 0.4)
- thickness: strength
- color: green/yellow/red by strength
- style: optional by synapse type (solid shared-entity; dashed intent-shift; dotted bridge)

---

## “Wrong intent” must be visible instantly

Add a UI rule for anchor training:
- if node.distance_to_target_intent > threshold OR perspective mismatch is high
  → show ⚠ badge and/or “danger zone” label near node.

This is not a ranking claim; it is a UX mechanism to prevent human mistakes.

---

## Map stability

For repeated runs:
- keep stable IDs for nodes (hash over normalized phrase + market + language)
- keep centroid positions per cluster when possible (layout damping)
- only allow small drift between runs unless data changes materially
