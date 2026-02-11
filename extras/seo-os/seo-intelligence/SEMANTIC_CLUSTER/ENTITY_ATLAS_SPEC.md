# ENTITY ATLAS – Intelligence Platform

## VISION v1.2 + PRD v1.0 + ENGINE SPEC v0.9

> **Status:** PLANNING → READY FOR BUILD (Phase 1.5 fokus: Rank Upload + Gap)

---

## 0) North Star (Measurable)

**Goal:** Build "THE ONLY" tool by combining two layers in a single data platform.

| Layer | Purpose |
|-------|---------|
| **Offline Core** | Deterministic semantic model that works on text alone, producing stable Entity/Cluster/Intent conclusions |
| **Online Verifier** | SERP + KG layer that produces evidence about Google's interpretation, can override offline hypotheses |

> **Axiom:** All "conclusion fields" MUST have Evidence. Without evidence = hypothesis, not truth.

### Verifiable Product Promise
The tool shall always answer two questions with evidence:
1. "What is this in Google's model?" → Entity Type + relations + SERP signals
2. "What am I missing to cover it?" → Coverage + gap clusters + priority

---

## 1) PRD v1.0

### 1.1 Target Audiences
SEO consultants, in-house SEO, content leads, affiliate teams, iGaming teams, agency research

### 1.2 JTBD
> "I want to go from 50 to 50,000 keywords and get: Entity-map (what the topic is), Cluster-map (how people search), Intent (why they search), Gaps (what I'm missing), Dominance (what #1 signals), and export as briefs and content plans."

### 1.3 Differentiators (vs InLinks, Keyword Insights, Keyword Cupid, MarketMuse)

| Differentiator | Why World-Class |
|----------------|-----------------|
| **Evidence as first-class object** | Every conclusion has `why + signals + sources` |
| **Determinism guarantees** | Stable entity_id, cluster_id between runs |
| **QA harness from day 1** | Measurable precision, stability, coherence |
| **Rank Upload + Competitive Gap** | "Truth layer" for what's actually happening |
| **Comparison View** | "online casino" vs "spela casino" – demo killer |
| **Offline/Online separation** | Fast + cheap, yet Google-accurate when verification enabled |

### 1.4 KPIs

| KPI | Target v1 |
|-----|-----------|
| Attribution Accuracy (Intent) | ≥ 0.80 precision INFO/COMMERCIAL |
| Entity Resolution Hit Rate | ≥ 0.60 KG match when enabled |
| Cluster Stability | ≥ 0.85 ARI on +10% keywords |
| Cluster Coherence | intra-sim − inter-sim ≥ 0.10 |
| Time to Insight | < 30s for 5000 keywords |

---

## 2) ENGINE SPEC v0.9

### 2.1 Hard Rules

| Rule | Description |
|------|-------------|
| R0 | Output/storage uses canonical objects only – no ad-hoc UI fields |
| R1 | All conclusions explainable via Evidence |
| R2 | Determinism: same input + same version → same IDs and labels |
| R3 | All import via central normalizer – NO manual CSV parsing |
| R4 | Attribution pipeline mandatory for all rank data and seed-lists |
| R5 | Online verification optional; its evidence never mixed with offline without explicit provenance |

### 2.2 Canonical Objects

#### 2.2.1 Project
```json
{
  "project_id": "proj_<ulid>",
  "name": "string",
  "default_country": "SE",
  "default_language": "sv",
  "created_at": "ISO8601",
  "engine_version": "0.9.0",
  "model_version": "1.0.0",
  "rules_version": "1.0.0",
  "settings": {
    "enable_online_verifier": false,
    "serp_provider": "none|serpapi|dataforseo",
    "kg_provider": "none|wikidata|googlekg|both"
  }
}
```

#### 2.2.2 Query
```json
{
  "query_id": "q_<sha1(normalized+country+language)>",
  "text": "spela casino",
  "language": "sv",
  "country": "SE",
  "normalized": {
    "text": "spela casino",
    "tokens": ["spela", "casino"],
    "head_term": "casino",
    "modifiers": ["spela"]
  }
}
```

#### 2.2.3 Entity
```json
{
  "entity_id": "e_<sha1(normalized_name+type_hint+language)>",
  "name": "Casino",
  "type": "PRODUCT|CONCEPT|BRAND|PERSON|PLACE|ORG|EVENT|OTHER",
  "aliases": ["online casino", "casino online"],
  "properties": [{"key": "string", "value": "string", "source": "string"}],
  "parent_entities": ["entity_id"],
  "child_entities": ["entity_id"],
  "related_entities": [{"entity_id": "string", "relation_type": "RELATED_TO", "strength": 0.0}],
  "calculated": {
    "semantic_mass": 0.0,
    "coverage_score": 0.0
  },
  "evidence": ["ev_<id>"]
}
```

**Semantic Mass Formula v1.1:**
```
SemanticMass(E) = α×log(1 + Σvolume(cluster_i)) + β×centrality(E) + γ×diversity(intent_distribution) + δ×evidence_strength
```
Where α=0.40, β=0.25, γ=0.20, δ=0.15 (tunable)

#### 2.2.4 Cluster
```json
{
  "cluster_id": "c_<sha1(sorted_keyword_ids+primary_entity_id+intent+engine_version_major)>",
  "label": "Spela casino",
  "keyword_ids": ["kw_<id>"],
  "intent": "INFO|COMMERCIAL|TRANS|NAV|LOCAL",
  "task_archetype": "definition|guide|compare|review|price|buy|signup|login|brand|other",
  "intent_modifier": "bäst|köpa|hur|var|pris|bonus|gratis|utan registrering",
  "primary_entity_id": "e_<id>",
  "secondary_entity_ids": ["e_<id>"],
  "cluster_role": "CORE|SUPPORT|BRIDGE",
  "metrics": {
    "total_volume": null,
    "avg_difficulty": null,
    "serp_features": []
  },
  "stability_signature": "sha1_of_member_keyword_ids",
  "evidence": ["ev_<id>"]
}
```

#### 2.2.5 Evidence (THE KEY DIFFERENTIATOR)
```json
{
  "evidence_id": "ev_<ulid>",
  "status": "STUB|FINALIZED",
  "claim": {
    "type": "INTENT|ENTITY_TYPE|CLUSTER_ASSIGNMENT|RELATION|PAGE_TYPE|SERP_HOMOGENEITY",
    "value": "COMMERCIAL"
  },
  "signals": [
    {"signal_type": "modifier_rule", "value": "contains('bästa') => COMMERCIAL", "weight": 0.25},
    {"signal_type": "serp_page_type_distribution", "value": {"category": 0.6, "guide": 0.2}, "weight": 0.35},
    {"signal_type": "embedding_similarity", "value": 0.78, "weight": 0.15}
  ],
  "contradictions": [
    {"signal_a": "modifier_rule", "signal_b": "serp_page_type", "delta": 0.3, "resolution": "serp_wins"}
  ],
  "provenance": {
    "layer": "OFFLINE|ONLINE",
    "source": "rules|embeddings|serpapi|dataforseo|googlekg|wikidata|upload",
    "source_ref": "optional",
    "observed_at": "ISO8601"
  },
  "score": {
    "confidence": 0.0,
    "contradiction_rate": 0.0,
    "calibration": "uncalibrated|calibrated_v1"
  }
}
```

#### 2.2.6 EntityResolution
```json
{
  "resolution_id": "er_<ulid>",
  "entity_id": "e_<id>",
  "candidate_sources": [
    {"source": "wikidata", "qid": "Q123", "label": "Casino", "confidence": 0.83},
    {"source": "googlekg", "kg_id": "kg:/m/...", "label": "Casino", "confidence": 0.71}
  ],
  "chosen": {"source": "wikidata", "ref": "Q123", "confidence": 0.83},
  "fallback": {"type": "internal_catalog", "ref": "internal:Casino"},
  "evidence": ["ev_<id>"]
}
```

#### 2.2.7 SERPObservation
```json
{
  "serp_obs_id": "s_<ulid>",
  "query_id": "q_<id>",
  "snapshot_date": "YYYY-MM-DD",
  "provider": "serpapi|dataforseo",
  "serp_features": ["PAA", "FeaturedSnippet", "LocalPack"],
  "top_results": [
    {"rank": 1, "url": "string", "title": "string", "domain": "string"}
  ],
  "page_type_distribution": {"guide": 0.4, "category": 0.4, "product": 0.2},
  "homogeneity_score": 0.0
}
```

#### 2.2.8 RankingImport (Canonical Schema)
```json
{
  "import_id": "imp_<ulid>",
  "project_id": "string",
  "source": "ahrefs|semrush|gsc|simple_keyword_list",
  "report_type": "organic_keywords|matching_terms|serp_overview|simple_keyword_list|...",
  "uploaded_at": "ISO8601",
  "site": {
    "domain": "string",
    "label": "mine|competitor",
    "competitor_group": "optional"
  },
  "metadata": {
    "detected_language": "sv|en|unknown",
    "date_range": {"from": "YYYY-MM-DD|null", "to": "YYYY-MM-DD|null"},
    "warnings": []
  },
  "rows": [
    {
      "keyword_id": "kw_<sha1(normalized+country+language)>",
      "keyword": "string",
      "position": "number|null",
      "url": "string|null",
      "volume": "number|null",
      "kd": "number|null",
      "traffic": "number|null",
      "serp_features": ["string"],
      "snapshot_date": "YYYY-MM-DD"
    }
  ]
}
```

#### 2.2.9 AttributedKeyword
```json
{
  "keyword_id": "kw_<id>",
  "keyword": "online casino bonus",
  "attribution": {
    "intent": "COMMERCIAL",
    "intent_confidence": 0.86,
    "task_archetype": "compare",
    "cluster_id": "c_<id>",
    "cluster_label": "Casino bonusar",
    "cluster_role": "CORE",
    "primary_entity_id": "e_<id>",
    "secondary_entity_ids": ["e_<id>"],
    "entity_confidence": 0.81
  },
  "evidence": ["ev_<id>"]
}
```

---

## 3) Modular Models

| Model | Input | Output |
|-------|-------|--------|
| **A: Normalize** | Query text | normalized, tokens, head_term, modifiers, language |
| **B: Intent Inference** | Query, optional SERP | intent + task_archetype + evidence |
| **C: Entity Extract** | Query, optional SERP/KG | primary entity, secondaries, types + evidence |
| **D: Cluster Builder** | Queries + vectors + entities | cluster_ids, labels, roles |
| **E: SERP Homogeneity** | SERPObservation | homogeneity score + dominant archetype |
| **F: Entity Resolution** | Entity candidate | resolution + confidence + fallback |
| **G: Competitive Gap** | AttributedKeywords + rankings | entity/cluster/intent gaps + priority |
| **H: Dominance Lens** | Focus keyword + competitor data | #1 footprint + underperforming gaps |
| **I: Impossible Bridge** | Publisher + target entity profiles | pivot chains + risk score |

---

## 4) State Machine: Job Orchestration

```
INTAKE → NORMALIZE → ATTRIBUTION → STORE → ANALYZE_GAP → FINALIZED
                                                    ↓
                                                 FAILED
```

```json
{
  "job_id": "job_<ulid>",
  "project_id": "string",
  "stage": "INTAKE|NORMALIZE|ATTRIBUTION|STORE|ANALYZE_GAP|FINALIZED|FAILED",
  "input": {"import_id": "imp_<id>"},
  "results": {},
  "errors": []
}
```

---

## 5) Central Ahrefs Normalizer (MANDATORY)

### Supported Report Types
- `serp_overview`, `organic_keywords`, `matching_terms`
- `matching_terms_clusters`, `matching_terms_parent_topic`
- `backlinks`, `referring_domains`, `organic_competitors`
- `best_by_links`, `internal_most_linked`
- `simple_keyword_list`

### Import Contract
```typescript
import { processAhrefsUpload } from '@core/normalizers/ahrefs-normalizer';

// NEVER manual CSV parsing
const result = await processAhrefsUpload(file, {
  domain: extractedDomain,
  label: 'mine' | 'competitor',
  competitor_group: optional
});

if (result.success) {
  await saveImport(userId, result);
  await triggerAttributionPipeline(result.import_id);
}
```

---

## 6) Gap Analysis: Killer Feature (Phase 1.5)

### Definitions
```
MineVisibility(E) = keywords in entity E where my position ≤ 20
CompetitorVisibility(E) = union of competitor keywords in E where position ≤ 20
EntityGap(E) = CompetitorVisibility(E) − MineVisibility(E)
```

### Priority Score v1
```
priority = Σ(volume_gap_kw) × (1 / (1 + avg_kd)) × serp_homogeneity × entity_importance
```

### Output Format
```json
{
  "entity_id": "e_<id>",
  "summary": {
    "mine_top20": 120,
    "competitor_top20": 340,
    "gap_keywords": 220,
    "priority_score": 4123.4
  },
  "by_intent": [...],
  "by_cluster": [...],
  "top_actions": [
    {"action_type": "create_page", "cluster_id": "c_<id>", "archetype": "compare", "why": "..."}
  ]
}
```

---

## 7) Database Schema v1 (Postgres)

| Table | Purpose |
|-------|---------|
| `projects` | Project settings |
| `imports` | Upload metadata |
| `import_rows` | Raw canonical rows |
| `queries` | Normalized queries |
| `entities` | Entity catalog |
| `entity_resolutions` | KG matches |
| `clusters` | Cluster definitions |
| `cluster_members` | Query↔Cluster links |
| `evidence` | Evidence records |
| `serp_observations` | SERP snapshots |
| `rank_observations` | Domain×keyword×snapshot |
| `keyword_attributions` | Enriched keywords |
| `entity_coverage_cache` | Precomputed coverage |
| `gap_cache` | Precomputed gaps |

---

## 8) Frontend: 3 World-Class Views First

| Priority | View | Key Features |
|----------|------|--------------|
| 1 | **Galaxy View** | Force graph, filters (intent/entity/role/confidence), evidence panel per node |
| 2 | **Entity Profile** | Properties, relations, intent distribution, clusters, gaps, export as brief |
| 3 | **Comparison View** | Side-by-side: overlap clusters, unique clusters, intent profile, dominance |

---

## 9) Roadmap as Gates

| Phase | Gate | Ship Criteria |
|-------|------|---------------|
| **1: Foundation** | Galaxy + Entity popup + Autocomplete expand + offline clustering + evidence panel | Basic exploration works |
| **1.5: Killer Feature** | Rank Upload + Attribution + Entity Gap + Dominance Lens | Gap scorecard for real data |
| **2: Entity Intelligence** | Entity resolution + properties + relations + semantic mass | KG integration |
| **3: Gap Analysis Pro** | Coverage scoring vs site URLs + competitor enrichment | Site-level analysis |
| **4: Professional** | Matrix view + bulk export + project save/load | Production workflows |
| **5: SERP Validation** | SERP alignment view + page-type classifier + PAA clustering | "Google lens" layer |

---

## 10) Build Order for Phase 1.5

1. Canonical Objects + DB schema v1
2. Ahrefs normalizer integration
3. Attribution Pipeline v1 with Evidence
4. Rank observations storage
5. Entity Gap Scorecard endpoint + UI
6. Dominance Lens endpoint + UI
7. Galaxy "coverage layer" overlay

---

## Appendix: Additional Constraints

| Constraint | Implementation |
|------------|----------------|
| Contradiction-rate in Evidence | `contradictions[]` array + `score.contradiction_rate` |
| Version separation | `engine_version`, `model_version`, `rules_version` in Project |
| Stability signature | `stability_signature` in Cluster for quick diff |
| Keyword ID as first-class | `keyword_id = sha1(normalized + locale)` used everywhere |
| Evidence lifecycle | `status: STUB → FINALIZED` (offline creates stub, online finalizes) |
