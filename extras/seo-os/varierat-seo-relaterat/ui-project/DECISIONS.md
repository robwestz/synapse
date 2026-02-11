# DECISIONS: SEO Intelligence UI

> Beslutlogg for projektet. Alla betydande beslut dokumenteras har.

---

## Aktiva beslut

| ID | Beslut | Motivering | Datum | Status |
|----|--------|------------|-------|--------|
| D001 | Bygg pa siex-dashboard (Vanilla JS) | Redan fungerar, Svelte-ready, har keyword extraction | 2025-12-30 | BEKRAFTAD |
| D002 | Live API direkt (ingen mock) | Snabbare iteration, testar verklig integration fran start | 2025-12-30 | BEKRAFTAD |
| D003 | MVP: Intent + Clustering + SERP | Mest varde, visar ML + SERP-kapacitet | 2025-12-30 | BEKRAFTAD |
| D004 | SIE-X for keyword extraction | Fungerar nu, API pa 8000, SDK tillgangligt | 2025-12-30 | BEKRAFTAD |
| D005 | Portkonfiguration: SIE-X=8000, ML=8003 | Foljer befintlig infrastruktur | 2025-12-30 | BEKRAFTAD |
| D006 | SERP-features krav extern datakalla | Alla SERP-features ar skelett, saknar _analyze_serp() | 2025-12-30 | BEKRAFTAD |
| D007 | Konvertera till Svelte stegvis | Dashboard ar "Svelte-ready", migrering efter MVP | 2025-12-30 | PLANERAD |

---

## Principer

### P1: SERP-data ar karna
Alla SERP-relaterade features ska ha tillgang till faktisk SERP-data.
Utan SERP-data ar dessa features vardelosa.

### P2: En feature = En modul
Varje feature far sin egen UI-modul med:
- Input-formulär
- API-anrop
- Resultatvisning
- Error handling

### P3: API-response synlig
Anvandaren ska kunna se ra API-response for debugging och transparens.

### P4: Progressiv komplexitet
Borja med enkla features, lagg till komplexitet iterativt.

### P5: Offline-fallback
Om API inte svarar, visa tydligt felmeddelande och senaste cachade resultat om tillgangligt.

---

## Oppna fragor

- [ ] Vilken SERP-datakalla ska anvandas? (SIE-X SEOTransformer, extern API, eller bada?)
- [ ] Ska siex-dashboard ateranvandas eller byggas fran scratch?
- [ ] Hur hanteras autentisering mot API:erna?
- [ ] Ska features grupperas efter kategori eller visas som flat lista?
- [ ] Behover vi WebSocket for live SERP monitoring?

---

## Beslut som behover fattas

### DF001: SERP-datakalla
**Alternativ:**
1. SIE-X SEOTransformer (inbyggd)
2. Extern SERP API (DataForSEO, SerpAPI, etc.)
3. Hybrid (SIE-X + extern for live data)

**Rekommendation:** Utred SIE-X forst, komplettera med extern vid behov

### DF002: Dashboard-arkitektur
**Alternativ:**
1. Bygg vidare pa siex-dashboard
2. Ny Svelte-app fran scratch
3. Integrera i befintlig struktur

**Rekommendation:** Undersok siex-dashboard forst

---

## Besluthistorik

### 2025-12-30: Projektstart
- Skapade bootstrap-artefakter
- Bekraftade MVP-scope
- Identifierade SIE-X som potentiell SERP-motor

---

*Format: D[NNN] = Beslut, P[N] = Princip, DF[NNN] = Beslut att fatta*