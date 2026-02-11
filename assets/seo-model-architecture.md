# SEO Intelligence: Komplett Modellarkitektur
## "Synapse Engine" — Från sökfras till visuell karta

Version: 2025-02-05 | Syfte: Universell modell för alla SEO-vertikaler

---

## 1. Arkitektur-översikt

```
┌──────────────────────────────────────────────────────────────────┐
│                    SYNAPSE ENGINE PIPELINE                        │
│                                                                  │
│  INPUT: 1 seed phrase + intent + market                          │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ M1: SEED │──→│ M2: CAND │──→│ M3: SCORE│──→│ M4: CLUST│     │
│  │ DECOMP   │   │ GENERATE │   │ & SELECT │   │ & MAP    │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│       │              │              │              │              │
│  ┌──────────┐   ┌──────────┐                 ┌──────────┐       │
│  │ M5: INTENT│   │ M6: ENTITY│               │ M7: VISUAL│      │
│  │ ENGINE   │   │ RESOLVER │                │ RENDERER │       │
│  └──────────┘   └──────────┘                └──────────┘       │
│                                                                  │
│  OUTPUT: 50 phrases + synapses + clusters + visual map           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. De 7 modellerna — vad de gör och varför

### M1: Seed Decomposition Model
**Roll:** Bryt ner startsökfrasen till alla sina dimensioner
**Varför:** Utan detta genererar LLM bara "varianter" istället för att
systematiskt täcka det semantiska rummet.

```yaml
seed_decomposition:
  input:
    phrase: string
    declared_intent: enum
    language: string
    market: string
    
  output:
    entities:
      - label: string
        type: enum [topic, brand, product, regulation, metric, action, attribute]
        kg_id: string | null  # Google KG ID om tillgängligt
    
    intent_profile:
      dominant: enum
      secondary: list[enum]
      perspective: enum [provider, seeker, advisor, regulator, neutral]
      # ↑ DETTA ÄR NYCKELN SOM SAKNAS I ALLA BEFINTLIGA MODELLER
      
    facets:
      # 10-20 dimensioner att expandera på
      - id: string
        label: string
        examples: list[string]
      # Ex: "kostnad", "risk", "jämförelse", "process", "regelverk"...
    
    hierarchy:
      parent_topic: string     # "lån" → "privatekonomi"
      sibling_topics: list     # "bolån", "billån", "snabblån"
      child_topics: list       # "ränta privatlån", "amortering privatlån"
    
    serp_prediction:
      expected_features: list  # [ads, paa, featured_snippet, local_pack...]
      expected_result_types: list  # [bank_sites, comparison, editorial, forum]
```

#### Varför "perspective" är avgörande

Det här är dimensionen som gör att ditt privatlåns-exempel fungerar:

```
"privatlån upp till 800 000"
  perspective: PROVIDER (banken erbjuder)
  intent: transactional
  
"betala av lån 800 000"
  perspective: SEEKER (låntagaren har problemet)
  intent: informational/problem_solving

"privatlån jämförelse 800 000"
  perspective: ADVISOR (jämförelsetjänst)
  intent: commercial_investigation

"regler privatlån belopp"
  perspective: REGULATOR/NEUTRAL
  intent: informational
```

Samma entiteter, helt olika perspektiv → helt olika klusterposition.
Google förstår detta implicit genom att SERP:arna ser helt annorlunda ut.
Vi gör det explicit genom att koda perspective som en första-klass-dimension.

---

### M2: Candidate Generation Model
**Roll:** Skapa en bred pool av 200-2000 kandidatfraser
**Varför:** 50 direkt ger för smal täckning. Du vill kunna VÄLJA 50 från
ett rikt urval.

```yaml
candidate_generation:
  sources:
    tier_1_ground_truth:
      - source: "google_ads_keyword_ideas"
        input: seed_phrase
        expected_yield: 100-500
        provenance: "ads_api"
        confidence: high
        
      - source: "gsc_query_report"
        input: site_url + seed_related_pages
        expected_yield: 50-300
        provenance: "gsc"
        confidence: high
        note: "Kräver sajt-kontext, inte alltid tillgängligt"
        
    tier_2_serp_derived:
      - source: "paa_questions"
        input: seed_phrase → Google SERP
        expected_yield: 8-20
        provenance: "serp_paa"
        
      - source: "related_searches"
        input: seed_phrase → SERP bottom
        expected_yield: 8-10
        provenance: "serp_related"
        
      - source: "autocomplete_suggestions"
        input: seed_phrase + alphabet expansion
        expected_yield: 50-200
        provenance: "autocomplete"
        
    tier_3_llm_expansion:
      - source: "pathway_traversal"
        method: "LLM genererar via 8 synapsvägar"
        expected_yield: 60-100
        provenance: "llm_inferred"
        confidence: medium
        note: "Valideras mot tier 1-2 i scoring"
        
      - source: "facet_expansion"
        method: "LLM expanderar varje facet från M1"
        expected_yield: 40-80
        provenance: "llm_inferred"
        
  deduplication:
    method: "fuzzy match + embedding cluster"
    threshold: 0.92  # cosine similarity
    keep: "variant med högst estimated volume"
    
  output:
    candidate_pool:
      - phrase: string
        provenance: enum [ads_api, gsc, serp_paa, serp_related, 
                          autocomplete, llm_inferred]
        raw_metrics:
          volume: int | null
          cpc: float | null
          competition: float | null
```

---

### M3: Relatedness Scoring & Selection Model
**Roll:** Ranka alla kandidater och välj de 50 mest relevanta+diversifierade
**Varför:** "Närmast relaterade" ≠ "mest lika". Du vill täckning av
det semantiska rummet, inte 50 varianter av samma fras.

```yaml
scoring_model:
  # Steg 1: Per-kandidat scoring mot seed
  relevance_score:
    components:
      entity_overlap:
        weight: 0.25
        method: "Jaccard på extraherade entiteter (seed vs kandidat)"
        source: "M6 entity resolver"
        
      serp_overlap:
        weight: 0.25
        method: "Jaccard på top-10 URL:er"
        source: "SERP API"
        fallback: "Om ej tillgängligt: embedding_similarity × 1.3"
        
      embedding_similarity:
        weight: 0.20
        method: "Cosine similarity, multilingual sentence-transformers"
        model: "paraphrase-multilingual-MiniLM-L12-v2"
        
      intent_compatibility:
        weight: 0.15
        method: "Intent-proximity score (se intent_distance_matrix)"
        source: "M5 intent engine"
        
      perspective_alignment:
        weight: 0.15
        method: "Perspektiv-match med seed (se perspective_distance)"
        source: "M1 seed decomposition"
        note: "DETTA ÄR DEN NYA DIMENSIONEN"

  # Steg 2: Intent distance matrix
  # (hur "långt" är det mellan intent-typer?)
  intent_distance_matrix:
    #                info  howto  comm   trans  nav    local  fresh
    informational: [0.0,  0.2,   0.4,   0.6,   0.8,   0.7,   0.3]
    howto:         [0.2,  0.0,   0.3,   0.5,   0.7,   0.6,   0.4]
    commercial:    [0.4,  0.3,   0.0,   0.2,   0.5,   0.4,   0.3]
    transactional: [0.6,  0.5,   0.2,   0.0,   0.4,   0.3,   0.5]
    navigational:  [0.8,  0.7,   0.5,   0.4,   0.0,   0.6,   0.7]
    local:         [0.7,  0.6,   0.4,   0.3,   0.6,   0.0,   0.5]
    freshness:     [0.3,  0.4,   0.3,   0.5,   0.7,   0.5,   0.0]

  # Steg 3: Perspective distance
  # (hur "långt" är det mellan avsändarroller?)
  perspective_distance:
    #              provider  seeker  advisor  regulator  neutral
    provider:     [0.0,     0.8,    0.4,     0.6,       0.3]
    seeker:       [0.8,     0.0,    0.3,     0.5,       0.2]
    advisor:      [0.4,     0.3,    0.0,     0.4,       0.2]
    regulator:    [0.6,     0.5,    0.4,     0.0,       0.3]
    neutral:      [0.3,     0.2,    0.2,     0.3,       0.0]
    
  # ↑ NOTERA: provider-seeker avstånd = 0.8 (maxnära max)
  # Det är DÄRFÖR "erbjuda privatlån" och "betala av lån" separeras.
    
  # Steg 4: Selection med MMR (Maximal Marginal Relevance)
  selection:
    target: 50
    method: "MMR"
    mmr_lambda: 0.75  # 0=max diversity, 1=max relevance
    constraints:
      max_same_intent: 15        # Inte 50 commercial-fraser
      max_same_perspective: 12   # Inte 50 provider-fraser
      max_near_duplicate: 3      # Stavningsvarianter
      min_bridge_phrases: 3      # Angränsande domäner
      min_intents_covered: 3     # Minst 3 olika intent-typer
```

---

### M4: Clustering & Topical Authority Mapping
**Roll:** Gruppera de 50 fraserna i visuellt distinkta kluster
**Varför:** DET HÄR ÄR VAD SOM GÖR MOLNET LÄSBART.
Utan klustring är 50 fraser bara en lista. Med klustring ser
en länkskribent DIREKT att "erbjuda lån" och "betala av lån"
är i olika delar av kartan.

```yaml
clustering_model:
  method: "Hierarchical clustering on composite distance matrix"
  
  distance_dimensions:
    # Klustret formas av ALLA dessa dimensioner, inte bara semantik
    semantic_embedding: 0.30
    intent_distance: 0.25
    perspective_distance: 0.25  # ← NYA dimensionen
    entity_overlap: 0.20
    
  parameters:
    target_clusters: "auto"  # Låt algoritmen bestämma (3-8 typiskt)
    min_cluster_size: 3
    max_cluster_size: 15
    
  labeling:
    method: "LLM labels based on dominant entities + intent + perspective"
    format:
      name: string          # "Ansöka om privatlån"
      dominant_intent: enum
      dominant_perspective: enum
      hub_entity: string    # Mest centrala entiteten i klustret
      
  # Topical Authority dimensions per kluster
  authority_mapping:
    per_cluster:
      content_depth: "Hur många sub-topics täcks?"
      intent_coverage: "Täcks alla relevanta intents?"
      entity_completeness: "Saknas viktiga entiteter?"
      internal_linking: "Hur bör klustret länkas internt?"
      
  output:
    clusters:
      - id: string
        label: string
        phrases: list[int]  # index i selected_50
        centroid: list[float]  # 2D-position för visualisering
        hub_entity: string
        dominant_intent: enum
        dominant_perspective: enum
        authority_gaps: list[string]  # Ämnen som saknas
        
    inter_cluster_bridges:
      # Phrases som kopplar kluster till varandra
      - phrase_id: int
        connects: [cluster_a, cluster_b]
        bridge_type: string
```

---

### M5: Intent Engine
**Roll:** Klassificera intent för varje fras, inklusive perspektiv
**Design:** 2-fas (deterministisk + LLM), precis som ChatGPT föreslog

```yaml
intent_engine:
  # Fas 1: Deterministisk pre-klassificering (0 LLM-cost)
  phase_1_rules:
    patterns:
      navigational:
        signals: ["logga in", "login", "kontakt", "kundtjänst", 
                  "app", "site:", "{brand_name}"]
        confidence: 0.8
        
      transactional:
        signals: ["ansök", "registrera", "köp", "boka", "spela",
                  "beställ", "teckna", "prenumerera"]
        confidence: 0.7
        
      commercial_investigation:
        signals: ["bästa", "bäst", "topplista", "jämför", "vs", 
                  "recension", "omdöme", "alternativ", "billigast"]
        confidence: 0.7
        
      informational:
        signals: ["vad är", "vad betyder", "hur funkar", "fakta",
                  "guide", "förklaring", "definition"]
        confidence: 0.7
        
      howto:
        signals: ["hur", "så gör du", "steg för steg", "tips",
                  "räkna ut", "beräkna"]
        confidence: 0.7
        
      problem_solving:
        signals: ["problem", "fungerar inte", "betala av", "lösa",
                  "hjälp med", "slippa", "undvika", "minska"]
        confidence: 0.6

    # Perspektiv-signals (NYA)
    perspective_signals:
      provider:
        signals: ["erbjuder", "upp till", "ansök hos oss", "våra",
                  "vi erbjuder", "välj bland"]
      seeker:
        signals: ["jag vill", "jag har", "jag behöver", "mitt",
                  "betala av", "hur gör jag", "kan jag"]
      advisor:
        signals: ["jämförelse", "bästa", "topp", "recension",
                  "vi har testat", "vår bedömning"]
      regulator:
        signals: ["regler", "lagkrav", "förordning", "tillsyn",
                  "konsumentskydd", "villkor"]

  # Fas 2: LLM Judge (med SERP-evidens om tillgängligt)
  phase_2_llm:
    trigger: "Alltid för selected_50; valfritt för candidate_pool"
    input:
      - phrase
      - locale
      - phase_1_hypotheses
      - serp_snapshot (om tillgängligt)
    output:
      dominant_intent: enum
      secondary_intents: list[enum]  # max 2
      perspective: enum
      confidence: float
      evidence: list[string]
      
    confidence_rules:
      high: "SERP-features + top-URLs stödjer klassificeringen"
      medium: "Modifier-match + entity-type stödjer"
      low: "Bara LLM utan extern evidens"
```

---

### M6: Entity Resolution Model
**Roll:** Mappa text till stabila entitets-ID:n med typ och disambiguation
**Varför:** "Lån" i "ta ett lån" och "lån" i "betala av ett lån" är samma
entitet men i olika relationskontext. Entity resolution ger stabilitet.

```yaml
entity_resolution:
  pipeline:
    step_1_extraction:
      method: "NER + noun phrase extraction"
      output: list of surface forms
      
    step_2_normalization:
      method: "Variant map (som din typo_and_variant_normalization)"
      output: canonical forms
      
    step_3_typing:
      types:
        - topic        # "privatlån", "amortering"
        - brand        # "SBAB", "Nordea"
        - product      # "privatlån 800 000"
        - regulation   # "konsumentkreditlagen"
        - metric       # "ränta", "effektiv ränta"
        - action       # "ansöka", "amortera", "jämföra"
        - attribute    # "billigast", "snabbast"
        - amount       # "800 000", "500 000"
        - person_role  # "låntagare", "långivare", "rådgivare"
        
    step_4_kg_lookup:
      method: "Google Knowledge Graph Search API"
      purpose: "Stabil ID + bekräftad entitetsstatus"
      fallback: "Intern hash-ID om ej i KG"
      
    step_5_relation_extraction:
      # VIKTIGT: inte bara identifiera entiteter, utan deras ROLL
      output:
        - entity_id: string
          canonical: string
          type: enum
          role_in_phrase: enum [subject, object, modifier, action]
          # "privatlån" kan vara SUBJECT (i "privatlån erbjudande")
          # eller OBJECT (i "ansök om privatlån")
```

---

### M7: Visual Rendering Model
**Roll:** Omvandla kluster + synapser till en karta som "läses utan text"
**Varför:** DET HÄR ÄR LEVERANSEN SOM SLUTANVÄNDAREN (länkskribenten) SER.
Allt annat är backend.

```yaml
visual_model:
  layout:
    algorithm: "Force-directed graph (d3-force) med kluster-gravity"
    dimensions: 2  # 2D-karta
    
    position_encoding:
      x_axis_primary: "intent spectrum (info ← → transactional)"
      y_axis_primary: "perspective spectrum (seeker ↑ → provider ↓)"
      # Så "ta lån" hamnar nere till höger (provider+transactional)
      # och "betala av lån" hamnar uppe till vänster (seeker+informational)
      
    cluster_encoding:
      color: "Unikt per kluster (kategorisk färgpalett)"
      proximity: "Fraser i samma kluster dras ihop av force"
      
    node_encoding:
      size: "Sökvolym (om tillgänglig) eller relevance_score"
      opacity: "Confidence (hög confidence = solid, låg = transparent)"
      border: "Provenance (ground truth = solid, LLM-only = dashed)"
      
    edge_encoding:
      thickness: "Synapse strength"
      style: "Synapse type (solid=entity_shared, dashed=intent_shift, 
              dotted=bridge)"
      visible: "Bara edges med strength > 0.4 (annars rörigt)"
      
    labels:
      node_label: "Sökfras (förkortad om > 30 tecken)"
      cluster_label: "Klusternamn + dominant intent-ikon"
      
    seed_highlight:
      style: "Pulsande ring runt seed-frasen"
      position: "Central"
      
  interactions:  # Om webbaserat
    hover: "Visa synapse card (varför kopplingen finns)"
    click: "Highlighta alla edges från noden"
    zoom: "Kluster-zoom (fokusera på ett kluster)"
    filter: "Visa/dölj per intent/perspective/provenance"

  # Statisk variant (för dokument/pdf)
  static_export:
    format: "SVG eller PNG"
    annotations:
      - "Intent-axel märkt med pilar"
      - "Perspektiv-axel märkt med pilar"
      - "Kluster-labels med bakgrund"
      - "Seed-fras markerad med stjärna"
      - "Legend: färger = kluster, storlek = volym/relevans"
```

---

## 3. Privatlåns-exemplet: Hur modellen löser det

### Input
```yaml
seed_phrase: "privatlån upp till 800 000"
seed_intent: "transactional"
language: "sv"
market: "SE"
domain_context: "finance/lending"
```

### M1 Output: Seed Decomposition
```yaml
entities:
  - {label: "privatlån", type: "product", role: "subject"}
  - {label: "800 000", type: "amount", role: "modifier"}
  - {label: "ansöka", type: "action", role: "implied"}

intent_profile:
  dominant: "transactional"
  secondary: ["commercial_investigation"]
  perspective: "provider"  # Erbjudande-formulering

facets:
  - {id: "cost", label: "Kostnad/ränta"}
  - {id: "eligibility", label: "Krav/villkor"}
  - {id: "comparison", label: "Jämförelse mellan långivare"}
  - {id: "process", label: "Ansökningsprocess"}
  - {id: "repayment", label: "Avbetalning/amortering"}
  - {id: "risk", label: "Risker/skuldfälla"}
  - {id: "regulation", label: "Regelverk/konsumentskydd"}
  - {id: "alternatives", label: "Alternativ (bolån, bilaga, osv)"}
  - {id: "amount_sizing", label: "Hur mycket ska jag låna?"}
  - {id: "refinancing", label: "Samla lån/refinansiering"}
```

### M4 Output: Predicted Clusters (förenklat exempel)

```
KLUSTER A: "Ansöka om privatlån" (transactional, provider)
  ├── privatlån ansökan
  ├── privatlån upp till 800 000
  ├── ansök privatlån online
  ├── privatlån utan UC
  ├── snabbt privatlån
  └── bästa ränta privatlån

KLUSTER B: "Jämföra privatlån" (commercial, advisor)
  ├── jämför privatlån
  ├── bästa privatlånet 2025
  ├── privatlån jämförelse ränta
  ├── billigast privatlån
  └── privatlån recension

KLUSTER C: "Hantera befintligt lån" (informational/problem, seeker)
  ├── betala av privatlån 800 000          ← HELT ANNAT KLUSTER
  ├── amortera privatlån snabbare
  ├── privatlån avbetalningsplan
  ├── räkna ut månadskostnad privatlån
  └── ångerrätt privatlån

KLUSTER D: "Ekonomisk planering" (informational, seeker)
  ├── hur mycket kan jag låna privatlån
  ├── löneberäkning privatlån
  ├── kvar att leva på privatlån
  ├── skuldsanering privatlån
  └── samla lån

KLUSTER E: "Regelverk & villkor" (informational, regulator/neutral)
  ├── konsumentkreditlagen privatlån
  ├── räntetak privatlån
  ├── villkor privatlån
  └── maxränta privatlån
```

### Visuellt:

```
        SEEKER (låntagaren)
            ↑
            │
     D ○○○  │  C ●●●
     Ekon.  │  Betala av
     plan   │  befintligt
            │
  ──────────┼──────────→ TRANSACTIONAL
            │
     E ○○   │  B ●●●●
     Regler │  Jämföra
            │
            │  A ●●●●●
            │  Ansöka
            │  ★ SEED
            ↓
        PROVIDER (långivaren)
```

Här SER länkskribenten att:
- "betala av lån 800 000" (kluster C, uppe till höger) 
  är LÅNGT IFRÅN seed-frasen (kluster A, nere till höger)
- De delar X-axel (transactional-ish) men Y-axeln skiljer totalt
- Rätt ankartext ska komma från kluster A eller B, INTE C eller D

---

## 4. Modeller som INTE behövs separat

ChatGPT listade 8 modeller. Jag har konsoliderat:

| ChatGPT:s modell | Min bedömning |
|---|---|
| A. Entity resolution | ✅ Behövs (M6) |
| B. Intent model | ✅ Behövs (M5) |
| C. SERP evidence | ⚡ Integrerad i M3 scoring, inte separat modell |
| D. Candidate gen | ✅ Behövs (M2) |
| E. Relatedness scoring | ✅ Behövs (M3) |
| F. Clustering | ✅ Behövs (M4) |
| G. Synapse explanation | ⚡ Integrerad i M3+M4 output, inte separat modell |
| H. Coverage/blueprint | 🔮 Bra men inte i MVP |

Mitt tillägg:
- M1 (Seed Decomposition) — saknas i ChatGPT:s lista men KRÄVS
- M7 (Visual Rendering) — saknas i ALLA modeller men är det som ger användar-värde
- **Perspective-dimensionen** — saknas överallt, löser Robins privatlåns-problem

---

## 5. Sammanfattning: Vad detta ger dig

### Differentiering mot alla befintliga verktyg:
1. **Intent + Perspective** som dubbel axel (inget verktyg gör detta)
2. **Synaps-förklaringar** med evidens (inte "related keywords" utan VARFÖR)
3. **Visuell karta** som icke-SEO-person förstår (inte en tabell)
4. **Universell modell** som fungerar för igaming, finans, e-com, SaaS...

### Vad som krävs för implementation:
- M1, M5, M6: Kan köras med enbart LLM (Gemini/Claude)
- M2: Kräver Ads API + valfritt SERP API för ground truth
- M3: Kräver sentence-transformers (kan köras lokalt) 
- M4: Standard clustering (scikit-learn/networkx)
- M7: d3.js / Plotly / Pyvis för visualisering

### Kvarvarande osäkerheter:
- Perspective-vikterna (0.15 i M3) behöver kalibreras mot riktiga SERP-data
- Perspective-signals i M5 behöver valideras per vertikal
- Visuell layout med 2-axlar (intent × perspective) kan bli trångt vid >50 noder
- MMR lambda (0.75) är en bra start men bör A/B-testas

### Nästa steg:
1. Validera perspective-modellen mot 5 vertikaler (finans, igaming, e-com, SaaS, hälsa)
2. Bygga M7 som interaktiv React-komponent
3. Skapa JSON-scheman för alla output-kontrakt
4. Testköra hela pipeline med "privatlån 800 000" som första case
