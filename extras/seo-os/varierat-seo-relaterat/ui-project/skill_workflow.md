# SKILL WORKFLOW GUIDE

> **En agnostisk guide for att anvanda CONSOLID-ramverket i komplexa projekt.**
>
> Placering: `seo-tool-skeletons/ui-project/`
> Version: 1.0.0
> Skapad: 2025-12-30

---

## SNABBREFERENS

```
FASORDNING:
0: Avsikt     -> Forsta malet
1: Kallor     -> Samla kunskap
2: Contracts  -> Definiera scheman
3: MVP        -> Leverera forsta version
4: Utokning   -> Bygg ut
5: Hardnande  -> Stabilisera

FILORDNING (LAS I DENNA ORDNING):
1. consolid/begin_here.md           <- Oversikt
2. consolid/claude.md               <- Systemprompt
3. consolid/MASTER_INDEX.md         <- Inventering
4. consolid/workflows/PHASES.md     <- Fasstruktur
5. consolid/checklists/QUALITY.md   <- Gates
6. [Relevant knowledge pack]        <- Domankunskap
```

---

## DEL 1: RAMVERKSOVERSIKT

### 1.1 Vad ar CONSOLID?

CONSOLID ar ett meta-ramverk for projekt som ar for komplexa for "en agent + en skill".

**Karnkomponenter:**
- **Framework**: Bootstrap-protokoll, recipes, ETL-mallar
- **Knowledge**: Skills, patterns, specifikationer
- **Tools**: Validators, generators, adapters
- **Workflows**: Faser med gates

**Principer:**
1. Bootstrap innan arbete - skapa stodartefakter forst
2. Schema forst - definiera output innan implementation
3. Skill-first design - spec innan kod
4. Validera allt - varje steg har regler
5. Context anchors - sammanfattningar for session-handoff

### 1.2 Mappstruktur

```
consolid/
|-- begin_here.md           # START HAR
|-- claude.md               # Systemprompt
|-- MASTER_INDEX.md         # Komplett inventering
|-- POLICIES.md             # Guardrails
|
|-- framework/              # Meta-protokoll
|   |-- PROJECT_BOOTSTRAP_PROTOCOL.md
|   |-- RECIPE_RUNNER_SPEC.md
|   |-- ETL_INSTRUCTION_TEMPLATE_v1.md
|   +-- LLM_PROJECT_FRAMEWORK_README.md
|
|-- knowledge/              # Domankunskap
|   |-- spec/               # SKILL_FORMAT, ENVELOPE_SPEC
|   |-- packs/              # SEO, docs, data-quality
|   |   |-- seo/skills/     # 12 SEO-skills
|   |   |-- docs/skills/    # 3 doc-skills
|   |   +-- data-quality/   # 3 datakvalitet-skills
|   +-- patterns/           # 21 agentic patterns
|
|-- tools/                  # Verktyg
|   |-- validators/         # validate-skill.py, etc.
|   |-- generators/         # new-pack.py, add-skill.py
|   +-- adapters/           # fs.sh, sqlite.py
|
|-- workflows/              # Faser
|   +-- PHASES.md
|
|-- checklists/             # Gates
|   +-- QUALITY.md
|
|-- templates/              # Mallar
|   |-- INTENT_SURVEY.md
|   |-- skill.template.md
|   +-- envelope.template.json
|
|-- quickstarts/            # 10 guider
|   +-- 01-10...
|
+-- logs/                   # Beslutshistorik
    +-- DECISIONS.md
```

---

## DEL 2: ARBETSFLODE

### 2.1 De 6 Faserna

| Fas | Namn | Mal | Gate (maste passeras) |
|-----|------|-----|----------------------|
| 0 | Avsikt & Scope | Forsta mal, constraints | Avsikt bekraftad |
| 1 | Kallor & Pack | Kurera docs, skapa pack | Pack finns |
| 2 | Data Contracts | Scheman + exempeldata | Validering passerar |
| 3 | MVP Leverans | Forsta korbar artefakt | QA passerar |
| 4 | Utokning | Fler features/rapporter | Regressionstest OK |
| 5 | Hardnande | Optimering, robusthet | Alla tester grona |

**KRITISKT**: Ga INTE vidare utan gate-acceptans!

### 2.2 Fasdetaljer

#### FAS 0: Avsikt & Scope

**Svar pa dessa fragor:**
1. Vad ar projektets primara mal? (1-2 meningar)
2. Vilken doman/industri?
3. Vilka artefakter ska levereras forst?
4. Vilka kallor/data har vi?
5. Begransningar? (tid, verktyg, sekretess, offline)
6. Hur vet vi att vi ar klara? (KPI/acceptans)
7. Komplexitet? (Enkelt/Medel/Komplext)

**Gate-checklista:**
- [ ] Mal dokumenterat
- [ ] Doman angiven
- [ ] Forsta leverabler listade
- [ ] Constraints kanda
- [ ] KPI definierad

#### FAS 1: Kallor & Pack

**Uppgifter:**
1. Identifiera relevanta docs/data
2. Valja eller skapa knowledge pack
3. Granska tillgangliga skills
4. Sakersstall att kallor ar citerbara

**Gate-checklista:**
- [ ] Pack eller docs-mapp identifierad
- [ ] Kallor citerbara (filavagar/ID)
- [ ] Inga oklara licenser/kanslighet

#### FAS 2: Data Contracts

**Uppgifter:**
1. Definiera output-scheman
2. Skapa sample-data
3. Validera mot schema

**Gate-checklista:**
- [ ] Scheman skrivna
- [ ] Sample-data finns
- [ ] Validering passerar utan fel

#### FAS 3: MVP Leverans

**Uppgifter:**
1. Implementera grundfunktionalitet
2. Bygga demo/prototyp
3. Grundlaggande felhantering

**Gate-checklista:**
- [ ] Korbart demo/prototyp/export
- [ ] Grundlaggande felhantering
- [ ] Minst ett testfall passerar

#### FAS 4: Utokning

**Uppgifter:**
1. Lagga till fler features
2. Utoka rapporter
3. Regressionstesta

**Gate-checklista:**
- [ ] Nya features dokumenterade
- [ ] Regressionstester korda
- [ ] Export/rapporter uppdaterade

#### FAS 5: Hardnande

**Uppgifter:**
1. Prestandaoptimering
2. Loggning/monitorering
3. Driftschecklista

**Gate-checklista:**
- [ ] Prestanda acceptabel
- [ ] Loggning definierad
- [ ] Driftschecklista ifylld

---

## DEL 3: PROJEKTSTART (BOOTSTRAP)

### 3.1 Bootstrap-protokollet

For MEDEL eller KOMPLEXT projekt, anvand bootstrap:

```
1. Ladda: consolid/framework/PROJECT_BOOTSTRAP_PROTOCOL.md
2. Sag: "Bootstrap projekt: [kort beskrivning]"
```

### 3.2 Genererade Artefakter

Bootstrap genererar:

| Artefakt | Syfte |
|----------|-------|
| `CONTEXT_ANCHOR.md` | Rod trad mellan sessioner |
| `GLOSSARY.md` | Terminologi som inte driftar |
| `DECISIONS.md` | Beslut som dokumenteras |
| `CHECKPOINTS.md` | Valideringspunkter |
| `RISKS.md` | Identifierade risker |

### 3.3 Komplexitetsbedomning

Bedoem projektet pa 5 dimensioner (1-5 vardera):

```
VOLYM:        [ ] Hur mycket data?
VARIATION:    [ ] Hur olika ar kallorna?
TOLKNING:     [ ] Hur mycket krav forstaelse?
BERIKNING:    [ ] Hur mycket extern kunskap behlovs?
VALIDERING:   [ ] Hur kritiskt ar korrekthet?

TOTAL: summa/25

> 15: Utokad bootstrap (alla artefakter)
8-15: Standard bootstrap
< 8:  Minimal bootstrap (glossary + schema)
```

---

## DEL 4: KUNSKAPSANVANDNING

### 4.1 Knowledge Packs

Valj pack baserat pa doman:

| Doman | Pack | Skills |
|-------|------|--------|
| SEO/Content | `knowledge/packs/seo/` | 12 skills |
| Dokumentation | `knowledge/packs/docs/` | 3 skills |
| Datakvalitet | `knowledge/packs/data-quality/` | 3 skills |

### 4.2 SEO Pack Skills (Detaljerad)

For SEO-projekt, dessa skills finns:

| Skill | Syfte | Anvandsnar |
|-------|-------|------------|
| `envelope-handler` | Parse/materialisera envelopes | Datahantering |
| `first-party-ingest` | GA4, GSC, logs -> metrics | Datainsamling |
| `render-crawler` | Crawla och auditera | Sajt-audit |
| `entity-reconciler` | Mappa till Wikidata | Entity-arbete |
| `competitive-modeler` | Konkurrensanalys | Strategi |
| `impact-forecaster` | Trafik/ROI-prediktion | Planering |
| `monitoring-agent` | Regression/diff-tracking | Overvakning |
| `quality-harness` | Content quality scoring | Kvalitet |
| `programmatic-factory` | Storskalig sidgenerering | Scale |
| `link-graph-analytics` | Intern lankanalys | Teknisk SEO |
| `schema-compiler` | JSON-LD generering | Schema markup |
| `delivery-devops` | Deployment automation | Deploy |

### 4.3 Patterns (21 st)

For workflow-design, anvand patterns fran `knowledge/patterns/`:

**Karna:**
- Prompt Chaining
- Routing
- Parallelization
- Reflection
- Tool Use

**Avancerat:**
- Planning
- Multi-Agent
- Memory Management

**System:**
- Goal Setting
- Exception Handling
- Human-in-the-Loop
- RAG

### 4.4 Skill Format (11 sektioner)

Varje skill foljer detta format:

```
1) Purpose          - Vad och varfor
2) Novelty rationale- Vad ar unikt
3) Trigger conditions - Nar anvanda
4) Prerequisites    - Foruts attningar
5) Sources          - Referenser
6) Conceptual model - Dataflode
7) Procedure        - Steg-for-steg
8) Artifacts produced - Output
9) Templates        - Mallar
10) Anti-patterns   - Undvik dessa
11) Integration     - Andra skills
```

---

## DEL 5: VERKTYG

### 5.1 Validators

```bash
# Validera en skill
python consolid/tools/validators/validate-skill.py <skill.md>

# Validera ett envelope
python consolid/tools/validators/validate-envelope.py <envelope.json>

# Validera ett helt pack
python consolid/tools/validators/validate-pack.py <pack-dir>
```

### 5.2 Generators

```bash
# Skapa nytt pack
python consolid/tools/generators/new-pack.py <name> --domain <domain>

# Lagga till skill i pack
python consolid/tools/generators/add-skill.py <pack-dir> --name "Name" --slug "slug"

# Generera envelope
python consolid/tools/generators/generate-envelope.py <pack-dir> --track T1

# Initiera projekt
python consolid/tools/generators/init-project.py <dir>
```

### 5.3 Adapters

| Adapter | Sprak | Backend |
|---------|-------|---------|
| `fs.sh` | Bash | Filesystem |
| `fs_and_sqlite.ps1` | PowerShell | FS + SQLite |
| `sqlite.py` | Python | SQLite |
| `webhook.js` | Node.js | HTTP Webhook |

---

## DEL 6: SESSION MANAGEMENT

### 6.1 Context Anchors

Korta sammanfattningar for att ladda om kontext:

```markdown
# CONTEXT ANCHOR: [PROJEKTNAMN]

## Enradsbeskrivning
[Max 100 tecken]

## Tre nyckelprinciper
1. [princip]
2. [princip]
3. [princip]

## Kritiska beslut
- D001: [kort]
- D002: [kort]

## Aktuellt lage
[Var ar vi? Nasta steg?]

## Roda flaggor
[trigger] -> [atgard]
```

### 6.2 Session Handoff

Vid ny session:
```
1. Ladda: CONTEXT_ANCHOR.md
2. Sag: "Ateruppta projekt [NAMN], fortsatt fran [checkpoint]"
3. LLM har full kontext
```

### 6.3 Beslutloggning

Vid betydande beslut:

```markdown
## D-[NNN] -- [Datum]
**Beslut**: [Vad beslutades]
**Skal**: [Varfor]
**Kalla**: [Filavag eller referens]
```

---

## DEL 7: CONSISTENCY CHECK

Innan major output, verifiera:

- [ ] **TERMINOLOGI**: Konsekvent med GLOSSARY.md?
- [ ] **BESLUT**: Foljer DECISIONS.md principer?
- [ ] **SCHEMA**: Matchar definierat format?
- [ ] **VALIDERING**: Passerar CHECKPOINTS.md?

Om inkonsekvent -> STOPPA och flagga.

---

## DEL 8: PRAKTISK CHECKLISTA

### 8.1 For nya projekt

```
[ ] 1. Las consolid/begin_here.md
[ ] 2. Besvara 7 intent-fragorna (Fas 0)
[ ] 3. Kor bootstrap om komplexitet >= Medel
[ ] 4. Identifiera relevanta skills/patterns
[ ] 5. Definiera scheman (Fas 2)
[ ] 6. Bygg MVP (Fas 3)
[ ] 7. Iterera genom fas 4-5
```

### 8.2 For aterupptagna projekt

```
[ ] 1. Ladda CONTEXT_ANCHOR.md
[ ] 2. Kontrollera senaste fas
[ ] 3. Granska DECISIONS.md
[ ] 4. Verifiera CHECKPOINTS.md
[ ] 5. Fortsatt fran aktuell fas
```

### 8.3 For stora projekt (som SEO UI)

```
[ ] 1. Bootstrap projekt
[ ] 2. Skapa projektspecifik GLOSSARY
[ ] 3. Mappa kravda skills
[ ] 4. Definiera komponentscheman
[ ] 5. Prioritera MVP-features
[ ] 6. Bygg i faser med gate-validering
[ ] 7. Dokumentera beslut kontinuerligt
```

---

## DEL 9: SNABBSTART FOR SEO UI-PROJEKTET

### 9.1 Projektkontext

**Mal**: Bygga UI for samtliga SEO-verktyg i seo-tool-skeletons

**Komponenter att integrera:**
- 46 standard features (`features/`)
- 21 avancerade features (`features_advanced/`)
- 6 ML-modeller (BERT, LightGBM, Word2Vec, LSTM, spaCy, Hybrid)
- REST API endpoints (FastAPI)

### 9.2 Foreslagna Faser

**Fas 0: Avsikt**
- UI-ramverk (React/Vue/Svelte?)
- Prioriterade features for MVP
- API-integration strategy

**Fas 1: Kallor**
- `seo-tool-skeletons/INVENTORY.md`
- `seo-tool-skeletons/README.md`
- `consolid/knowledge/packs/seo/`

**Fas 2: Contracts**
- UI-komponentschema
- API-response format
- State management schema

**Fas 3: MVP**
- Dashboard med 5-10 karnfunktioner
- Intent classification UI
- Content scoring UI
- Keyword clustering UI

**Fas 4: Utokning**
- Resterande 40+ features
- Avancerade ML-features
- Rapportering/export

**Fas 5: Hardnande**
- Performance optimization
- Error handling
- Production deployment

### 9.3 Forslag pa Intent-Svar

```
1. MAL: Bygga ett komplett UI for SEO Intelligence Platform
   som exponerar alla 67 ML/SEO-features via webgranssnitt.

2. DOMAN: SEO, Machine Learning, Web Development

3. LEVERABLER:
   - Dashboard med feature-oversikt
   - Intent classification modul
   - Content scoring modul
   - Keyword clustering modul
   - Traffic prediction modul
   - Recommendations engine UI

4. KALLOR:
   - seo-tool-skeletons/ (67 features, 6 modeller)
   - consolid/knowledge/packs/seo/ (12 skills)
   - API-dokumentation pa /docs

5. CONSTRAINTS:
   - Python 3.11+ backend
   - FastAPI pa port 8003
   - Modeller saknas (behover traningsdata)

6. ACCEPTANS:
   - Alla API-endpoints narbara via UI
   - Response-tider <2s for standard features
   - Fungerar offline efter initial load

7. KOMPLEXITET: Komplext (veckor)
```

---

## DEL 10: REFERENSER

### 10.1 Nyckelfilref

| Fil | Anvaendning |
|-----|-------------|
| `consolid/begin_here.md` | Startpunkt |
| `consolid/claude.md` | Systemprompt |
| `consolid/MASTER_INDEX.md` | Inventering |
| `consolid/workflows/PHASES.md` | Fasstruktur |
| `consolid/checklists/QUALITY.md` | Gates |
| `consolid/framework/PROJECT_BOOTSTRAP_PROTOCOL.md` | Bootstrap |
| `consolid/knowledge/spec/SKILL_FORMAT.md` | Skill-format |
| `consolid/templates/INTENT_SURVEY.md` | Intent-fragor |

### 10.2 Kommandoreferens

```bash
# Validators
python consolid/tools/validators/validate-skill.py <file>
python consolid/tools/validators/validate-envelope.py <file>
python consolid/tools/validators/validate-pack.py <dir>

# Generators
python consolid/tools/generators/new-pack.py <name> --domain <d>
python consolid/tools/generators/add-skill.py <dir> --name --slug
python consolid/tools/generators/generate-envelope.py <dir> --track
python consolid/tools/generators/init-project.py <dir>
```

### 10.3 Quickstart-guider

| # | Guide | Amne |
|---|-------|------|
| 01 | knowledge-pack-and-schema | Pack + schema |
| 02 | mvp-data-roundtrip | MVP data roundtrip |
| 03 | multi-agent-division | Multi-agent |
| 04 | offline-doc-consumption | Offline docs |
| 05 | kpi-and-acceptance | KPI |
| 06 | export-pipeline | Export |
| 07 | ci-bootstrap | CI |
| 08 | risk-log-and-policies | Risk |
| 09 | offline-benchmark | Benchmark |
| 10 | handoff-and-traceability | Handoff |

---

## APPENDIX A: PROJEKTMALL

```markdown
# [PROJEKTNAMN]

## Projektinfo
- Startdatum: YYYY-MM-DD
- Fas: [0-5]
- Komplexitet: [Enkelt/Medel/Komplext]

## Avsikt
[Svar pa 7 intent-fragorna]

## Aktiva beslut
[Kopierat fran DECISIONS.md]

## Nasta steg
- [ ] [Uppgift 1]
- [ ] [Uppgift 2]

## Session-historik
| Datum | Fas | Checkpoint | Anteckningar |
|-------|-----|------------|--------------|
```

---

## APPENDIX B: TROUBLESHOOTING

### Problem: Tappar kontext mellan sessioner
**Losning**: Anvand CONTEXT_ANCHOR.md konsekvent

### Problem: Inkonsekvent terminologi
**Losning**: Skapa och referera GLOSSARY.md

### Problem: Osaker pa vilken fas
**Losning**: Kontrollera CHECKPOINTS.md, kor gate-validering

### Problem: Stora projekt blir ooverskadliga
**Losning**: Bryt ner i mindre leverabler, validera per fas

### Problem: Beslut fattas inkonsekvent
**Losning**: Logga ALLA beslut i DECISIONS.md

---

*CONSOLID -- Projekt som vore omojliga for en agent + en skill blir mojliga.*

*Skapad: 2025-12-30 | Version: 1.0.0*