# Anchor Safety — Prevent Wrong-Intent Links

This is the “content-team” layer: the system should warn when an anchor phrase belongs to a different cluster than the target page’s dominant interpretation.

## Why it matters
Two phrases can share entities but be semantically far apart:

- Target (provider/product offer): “privatlån upp till 800 000”
- Bad anchor (seeker/problem): “jag har ett lån på 800 000 jag ska betala av”

A non-SEO writer might think “same words = same topic”.  
The map should show: **different cluster → do not anchor**.

---

## Target Page Intent Profile (TPIP)

Compute TPIP per target URL using any available signals (partial is ok):

1) On-page (title, H1, CTA verbs, schema types)
2) SERP result type for that URL (bank page / comparison / editorial / regulator)
3) Internal linking context (what pages link to it, with what anchors)
4) Content sections (eligibility, apply, pricing, FAQs)

Output:
- dominant_intent
- perspective
- allowed_intents (optional)
- allowed_perspectives (optional)
- key entities (product/brand/amount/feature)
- “conversion verbs” (apply, sign up, buy, book, register)

---

## Anchor Safety Score

For anchor phrase `A` and target profile `T`:

distance = wI * intent_distance(A.intent, T.intent)
         + wP * perspective_distance(A.perspective, T.perspective)
         + wE * (1 - entity_overlap(A, T))
         + wS * (1 - serp_overlap_proxy(A, T))  # if you have SERP snapshots

Policy:
- PASS: distance <= 0.35
- WARN: 0.35 < distance <= 0.55  (allowed only if editorial rationale is provided)
- FAIL: distance > 0.55          (wrong cluster for anchor)

Return a human-readable explanation:
- “Same entity, different task”
- “Target is provider offer; anchor is seeker repayment”
- “SERP layouts differ strongly”

---

## Training UX pattern (what your screenshot already hints at)
- Hover shows synapse card (why connected)
- Weak cross-cluster edge triggers ⚠ “FEL KLUSTER FÖR ANKARTEXT”
- Recommended anchor pools: show top nodes in PASS zone, grouped by cluster

This turns “intent” into something *visual* and *unmissable*.
