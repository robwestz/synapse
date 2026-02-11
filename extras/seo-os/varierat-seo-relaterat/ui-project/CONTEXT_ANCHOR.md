# CONTEXT ANCHOR: SEO Intelligence UI

> Ladda denna fil vid varje ny session for att aterfa projektkontext.

---

## Enradsbeskrivning

Dashboard-UI for 67 SEO/ML-features med SIE-X och SERP-integration.

---

## Tre nyckelprinciper

1. **Live API First** - Koppla direkt mot SIE-X (8000) och ML-service (8003), ingen mock
2. **SERP-Centrerad** - SERP-data ar karnan - features utan SERP-koppling ar sekundara
3. **Svelte + Enkel arkitektur** - Minimal komplexitet, reaktiv state, snabb iteration

---

## Projektstruktur

```
seo-tool-skeletons/
├── ui-project/              <- VI BYGGER HAR
│   ├── skill_workflow.md    <- Workflow-guide
│   ├── CONTEXT_ANCHOR.md    <- Du laser just nu
│   ├── GLOSSARY.md          <- Terminologi
│   ├── DECISIONS.md         <- Beslut
│   └── CHECKPOINTS.md       <- Gates
│
├── SIE-X/                   <- KARNBEROENDE
│   ├── sie_x/api/           <- REST API (port 8000)
│   ├── sie_x/sdk/           <- Python SDK
│   ├── sie_x/transformers/  <- SEOTransformer
│   └── siex-dashboard/      <- Befintlig dashboard?
│
├── features/                <- 46 STANDARD FEATURES
├── features_advanced/       <- 21 AVANCERADE
├── models/                  <- 6 ML-MODELLER
└── routers/                 <- API ENDPOINTS
```

---

## Kritiska beslut

| ID | Beslut | Status |
|----|--------|--------|
| D001 | Svelte som frontend-ramverk | PRELIMINAR |
| D002 | Live API (ingen mock) | BEKRAFTAD |
| D003 | MVP: Intent + Clustering + SERP | BEKRAFTAD |
| D004 | SIE-X som keyword/SERP-motor | UTREDS |

---

## MVP Features (Prioritet 1)

1. **Intent Classification** - BERT-baserad (ML-service)
2. **Keyword Clustering** - Word2Vec + K-means (ML-service)
3. **SERP Analysis** - 6 verktyg (krava SERP-data)
4. **Keyword Extraction** - SIE-X API

---

## Aktuellt lage

**Fas:** 0 -> 1 (Bootstrap -> Kallor)
**Senaste aktivitet:** Bootstrap-artefakter skapade
**Nasta steg:**
1. Kartlagga SERP-beroende features
2. Undersoka siex-dashboard
3. Definiera komponentschema

---

## API Endpoints (bekraftade)

| Service | Port | Bas-URL | Docs |
|---------|------|---------|------|
| SIE-X | 8000 | /extract, /api/v1/* | /docs |
| ML-Service | 8003 | /api/v1/* | /docs |

---

## Roda flaggor

| Om du ser... | Gor detta... |
|--------------|--------------|
| SERP-feature utan datakalla | Koppla till SIE-X SEOTransformer |
| Port 8003 vs 8000 konflikt | ML=8003, SIE-X=8000 |
| Modeller saknas | Anvand mock/fallback tills tranade |
| `_analyze_serp()` ej implementerad | Behover SIE-X eller extern SERP API |

---

## Session Handoff

Vid ny session, sag:
```
Ateruppta projekt SEO Intelligence UI.
Las CONTEXT_ANCHOR.md.
Fortsatt fran [aktuell fas/checkpoint].
```

---

*Skapad: 2025-12-30 | Version: 1.0.0*