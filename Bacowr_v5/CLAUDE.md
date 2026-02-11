# BACOWR v5.6 — Claude Code Instruktioner

> **System**: Artikelgenerering + Utbildningsmaterial för SEO-länkstrategi
> **Version**: 5.6 (2026-01-29)

---

## Systemets Roll

Du arbetar med BACOWR v5.6 — ett system för att:

1. **Producera artiklar** med ankar- och trustlänkar för SEO
2. **Skapa utbildningsmaterial** om länkstrategi, ankartexter och målsidesplanering
3. **Analysera publiceringsstrategier** för optimal länkplacering

---

## Filstruktur & Navigation

```
v5/
├── CLAUDE.md                  ← DENNA FIL
├── SYSTEM.md                  ← Alla artikelregler (LÄS FÖRST vid artikeljobb)
├── AGENT_INSTALLATION.md      ← Komplett installationsguide
├── INIT.md                    ← Snabb översikt / crash recovery
├── README.md                  ← Teknisk snabbstart
│
├── pipeline.py                ← CSV → preflight → artikelprompt
├── models.py                  ← Datamodeller
├── rename_and_convert.py      ← Rename + DOCX (generisk)
├── requirements.txt           ← Python-beroenden
│
├── articles/                  ← Output: genererade artiklar
├── docx_export/               ← Output: DOCX-versioner
├── preflight/                 ← Output: semantisk analys (JSON)
├── prompts/                   ← Output: artikelprompts
│
└── guides/                    ← UTBILDNINGSMATERIAL
    ├── ankartext-och-malsides-planering.md  ← Del 1: Grundläggande principer
    ├── bridges-och-kontextlankar.md         ← Del 2: Kontextlänkar & bryggstrategi
    ├── kvalitetskontroll-och-optimering.md  ← Del 3: QA, arbetsflöde & vanliga misstag
    ├── komplett-utbildning.md               ← Allt i en fil (25+ sidor)
    ├── quick-reference-guide.md             ← Snabbreferens (1 sida)
    ├── utbildningsmoment.md                 ← Detaljerad lista över utbildningsmoment
    ├── utbildningsmoment-punktlista.md      ← Kortfattad punktlista
    └── docx/                                ← DOCX-versioner för delning
```

---

## Arbetssätt: Två Huvudmodus

### Modus 1: Artikelproduktion (SEO-texter)

**Workflow:**
1. Läs `SYSTEM.md` i sin helhet
2. Få input (CSV-rad ELLER manuella parametrar):
   - `publisher_domain` — sajten artikeln publiceras på
   - `target_url` — kundens målsida som ankarlänken pekar till
   - `anchor_text` — texten i ankarlänken (1-80 tecken)
3. Analysera gapet mellan publisher och target
4. **KRITISKT**: Hitta kontextlänkar (context boosters) som BINDER publisher och target
5. Formulera artikelns TES (en mening som hela texten driver)
6. Skriv artikeln (900+ ord, strukturerad, röd tråd)
7. Generera obligatorisk kvalitetskontrolltabell
8. Spara som `articles/job_NN.md`

**Kommando från användare:**
> "Kor jobb 14 från min_lista.csv"
> "Skriv artikel för sportligan.se → happycasino.se med ankartext 'Happy Casino'"

**Pipeline-stöd (valfritt):**
```bash
python pipeline.py run --csv path/to/jobs.csv --job 14
# Genererar preflight_014.json + prompt_014.md som guide
```

---

### Modus 2: Utbildningsmaterial (Förklaringar & Guides)

**Användningsfall:**
- Förklara hur ankartexter planeras för bästa SEO-resultat
- Instruera om målsidesanalys och publiceringsstrategi
- Skapa dokumentation om var texter ska publiceras på vilka sajter
- Pedagogiska exempel på kontextlänk-strategier

**Workflow:**
1. Identifiera vad som ska förklaras (t.ex. "Hur planerar man ankartexter?")
2. Använd BACOWR-principerna som grund:
   - Kontextlänklogiken (publisher → context booster → target)
   - Semantisk distans och bryggor
   - Kvalitetskontroll och verifieringsprocessen
3. Strukturera materialet pedagogiskt:
   - Tydliga exempel från verkliga fall
   - Före/efter-jämförelser
   - Visuella förklaringar med text-diagram
4. Spara i lämpligt format (markdown för dokumentation, presentationsformat för workshops)

**Exempel på utbildningsfrågor du kan besvara:**

<details>
<summary>Fråga: "Hur planerar man ankartexter och målsidor för bästa resultat?"</summary>

**Svar baseras på BACOWR-principerna:**

### Steg 1: Analysera målsidan
- Vilka entiteter och sökord vill kunden ranka för?
- Vilka LSI-termer och underämnen finns i målsidans kontext?
- Vilket search intent adresserar sidan?

### Steg 2: Välj ankartexten
- **EJ "klicka här"** — använd relevant sökord/begrepp
- 1-80 tecken, naturligt språk
- Måste matcha målsidans innehåll

### Steg 3: Identifiera publiceringsplattform
- Vilken sajt har vi tillgång till? (publisher_domain)
- Vad är dess naturliga ämnesområde?
- Hur långt är det från kundens sökintention?

### Steg 4: Bygg bryggan (kontextlänkar)
- Gapet = avståndet mellan publisher och target
- Om gapet är litet: en kontextlänk räcker
- Om gapet är stort: två kontextlänkar behövs
- Varje kontextlänk flyttar artikelns ämne närmare kundens sökintention

### Steg 5: Verifiera strategin
- Kan ankarlänken sitta naturligt i texten?
- Stärker kontexten målsidans topical authority?
- Är källorna (kontextlänkarna) verifierade och relevanta?

**Exempel:**
Publisher: byggtidning → Target: belysning (Rusta)
→ Kontextlänk: guide om belysningsplanering vid renovering
→ Nu kan ankarlänken "belysningssortiment" sitta naturligt
</details>

---

## Kärnkoncept (Viktigt att Förstå)

### 1. Kontextlänkar (Context Boosters)
**EJ dekoration — de är BRYGGAN mellan publisher och target.**

- Publisherdomänen sätter taket för hur nära kundens sökintention du kan komma
- Kontextlänkarna flyttar taket närmare
- Du letar inte efter "en bra källa" utan "källan som binder publisher och target samman"

**Exempel:**
- **Utan kontextlänk**: Byggsajt → renovering → länk till belysning (svag koppling)
- **Med kontextlänk**: Byggsajt → renovering → [KÄLLA om belysningsplanering vid renovering] → länk till belysningssortiment (stark koppling)

### 2. Tesformulering (Obligatorisk)
**EN mening som hela artikeln driver.**

Innan du skriver: Formulera artikelns tes. Varje sektion måste underbygga, komplicera eller fördjupa denna tes.

**Exempel:**
> "Morsdagsbuketten överlever alla trender för att den är inbäddad i själva högtiden — från datumvalet till dagens blombudslogistik."

Med den tesen vet du vad varje stycke ska göra.

### 3. Röd Tråd
**Sektioner måste bygga på varandra, inte vara utbytbara.**

- Strukturera efter relevans, EJ kronologi
- Sista meningen i varje stycke pekar framåt
- Första meningen i nästa stycke plockar upp tråden

### 4. Semantisk Distans
Pipeline.py beräknar embedding-baserad cosine-similarity:

| Avstånd | Tolkning | Handling |
|---------|----------|----------|
| ≥ 0.90 (identical) | Samma ämne | Direkt koppling |
| ≥ 0.70 (close) | Närliggande | Gemensamma entiteter räcker |
| ≥ 0.50 (moderate) | Viss koppling | Behöver tydlig bridge |
| ≥ 0.30 (distant) | Svag koppling | Explicit variabelgifte-strategi |
| < 0.30 (unrelated) | Ingen koppling | Varning — risken är hög |

### 5. Kvalitetskontroll
**Obligatorisk tabell i slutet av varje artikel.**

Kontrollerar:
- Ordantal (≥ 900)
- Ankarlänk position (ord 150-700)
- Kontextbrygga (hur väl kontextlänkarna binder publisher→target)
- Röd tråd (hänger sektionerna ihop?)
- AI-markörer (inga förbjudna fraser)
- Entity coverage

---

## Verktyg & Kommandon

### Python Pipeline (Preflight-analys)

```bash
# Alla jobb i en CSV
python pipeline.py run --csv path/to/jobs.csv

# Enskilt jobb
python pipeline.py run --csv path/to/jobs.csv --job 14

# Intervall
python pipeline.py run --csv path/to/jobs.csv --start 1 --end 10

# Endast preflight (ingen artikel)
python pipeline.py run --csv path/to/jobs.csv --preflight-only
```

**Output:**
- `preflight/preflight_NNN.json` — Semantisk analys
- `prompts/prompt_NNN.md` — Färdig artikelprompt

### Verktyg: Publisher-analys

```bash
python pipeline.py publisher sportligan.se
```

**Output:**
```json
{
  "domain": "sportligan.se",
  "site_name": "Sportligan",
  "topics": ["fotboll", "sport", "allsvenskan"],
  "language": "sv",
  "confidence": 0.7
}
```

### Verktyg: Target-analys

```bash
python pipeline.py target https://happycasino.se/
```

**Output:**
```json
{
  "url": "https://happycasino.se/",
  "title": "Happy Casino - Spela Online",
  "keywords": ["casino", "spela", "bonus"],
  "topic_cluster": ["spelautomater", "livecasino", "bonus"]
}
```

### Verktyg: Semantisk distans

```bash
python pipeline.py distance \
  --pub-topics fotboll sport \
  --tgt-keywords casino spel \
  --anchor "Happy Casino"
```

**Output:**
```json
{
  "distance": 0.45,
  "category": "moderate",
  "recommended_angle": "sportstatistik → analys → realtidsdata",
  "bridges": [...]
}
```

### Rename + DOCX-export

```bash
# Alla artiklar
python rename_and_convert.py --csv path/to/jobs.csv

# Enskilt jobb
python rename_and_convert.py --csv path/to/jobs.csv --job 14
```

**Skapar:**
- Omdöpta markdown-filer: `NNN_brand_publisher_rubrikslug.md`
- DOCX-versioner i `docx_export/`

---

## Förbjudna AI-Markörer

**ANVÄND ALDRIG:**
- "Det är viktigt att notera"
- "I denna artikel kommer vi att"
- "Sammanfattningsvis kan sägas"
- "Låt oss utforska"
- "I dagens digitala värld"
- "Det har blivit allt viktigare"
- "Har du någonsin undrat"
- "I den här guiden"

**Varför?** Avslöjar direkt att texten är AI-genererad.

---

## Batch-körning (Parallella Agenter)

För många artiklar samtidigt:

```bash
# 25 artiklar parallellt
for i in $(seq 1 25); do
  claude --background "Läs v5/SYSTEM.md. Kör jobb $i från min_lista.csv. Spara som v5/articles/job_$(printf '%02d' $i).md"
done

# Vänta, sedan nästa omgång
for i in $(seq 26 50); do
  claude --background "Läs v5/SYSTEM.md. Kör jobb $i från min_lista.csv. Spara som v5/articles/job_$(printf '%02d' $i).md"
done
```

**Rate limits**: 25 parallella agenter fungerar. Typisk tid: 15-30 min för 25 artiklar.

---

## Användningsexempel

### Exempel 1: Artikelproduktion (Interaktiv)

**Användare:**
> "Skriv artikel för sportligan.se → happycasino.se, ankartext 'Happy Casino'"

**Du gör:**
1. Läs `SYSTEM.md`
2. Analysera publisher (sportligan.se → sport, fotboll)
3. Analysera target (happycasino.se → casino, spel)
4. Semantisk distans: moderate (0.45)
5. Hitta kontextlänkar med WebSearch:
   - Sök: "sportstatistik betting analys"
   - WebFetch verifiering
   - Extrahera fakta
6. Formulera tes: *"Sportstatistik har blivit betting-analytikernas viktigaste verktyg — från Expected Goals till spelarbörsvärden."*
7. Skriv artikel (struktur: intro → bakgrund → fördjupning → koppling med ankarlänk → perspektiv → avslutning)
8. Generera QA-tabell
9. Spara som `articles/job_XX.md`

### Exempel 2: Utbildningsmaterial

**Användare:**
> "Förklara hur man planerar ankartexter och målsidor för bästa SEO-resultat med länkar"

**Du gör:**
1. Skapa guide baserad på BACOWR-principerna
2. Inkludera konkreta exempel:
   - Före/efter-jämförelser
   - Olika publisher-target-kombinationer
   - Gap-analys och bryggor
3. Visualisera med text-diagram:
   ```
   Publisher (byggtidning) → GAP → Target (belysning)
                ↓
           [Context Booster]
           Guide: Belysningsplanering vid renovering
                ↓
   Naturlig ankarlänk-placering
   ```
4. Spara som `guides/ankartext-planering.md`

### Exempel 3: Publiceringsstrategi

**Användare:**
> "Analysera var vi ska publicera texter om casino på vilka sajter"

**Du gör:**
1. Läs `SYSTEM.md` sektion 3 (Kärnlogiken)
2. Lista tillgängliga publishers (från CSV eller manuell input)
3. Beräkna semantisk distans för varje publisher → casino
4. Identifiera vilka publishers som:
   - Behöver 0 kontextlänkar (direct match)
   - Behöver 1 kontextlänk (moderate gap)
   - Behöver 2 kontextlänkar (large gap)
   - Ej rekommenderas (unrelated)
5. Skapa prioriteringsmatris:
   ```markdown
   | Publisher | Distans | Brygga | Prioritet |
   |-----------|---------|--------|-----------|
   | sportligan.se | 0.45 | sportstatistik → odds | HÖG |
   | golfligan.se | 0.38 | premium → upplevelse | MEDEL |
   | villanytt.se | 0.22 | — | LÅG (risk) |
   ```
6. Spara som `strategies/casino-publicering-analys.md`

---

## Integration med Agent Framework

Detta system lever i `gpt-system-teknisk-dokumentation/v5/` men kan användas från huvudprojektets agent-framework:

```bash
# Från root (C:\Users\robin\OneDrive\agent)
cd gpt-system-teknisk-dokumentation/v5

# Kör pipeline
python pipeline.py run --csv ../../path/to/jobs.csv

# Generera artiklar (referera till v5/SYSTEM.md)
# Claude Code kommer att läsa denna claude.md automatiskt när du arbetar i v5/
```

---

## Felsökning

| Problem | Lösning |
|---------|---------|
| CSV hittas inte | Ange fullständig sökväg med `--csv` |
| WebFetch blockerad | Bakgrundsagenter har begränsad WebFetch. Kör interaktivt. |
| Rate limit | Minska parallella agenter till 10-15 |
| Preflight crashar | Kontrollera att `sentence-transformers` är installerat |
| DOCX-export misslyckas | `pip install python-docx` |
| Artikel för kort | SYSTEM.md kräver 900+ ord. Förläng. |
| Ankarlänk fel position | QA-tabellen visar position. Flytta mellan ord 150-700 |
| Svag kontextbrygga | Hitta nya kontextlänkar som bättre binder publisher→target |

---

## Prioritetsordning vid Konflikter

Om instruktioner krockar:

1. **Säkerhet** — Aldrig förhandlingsbart
2. **Hårda krav** — Ankarlänk, ordantal, verifierade källor
3. **Kvalitet** — Checklistan (QA-tabell)
4. **Stil** — Skrivriktlinjer (SYSTEM.md)
5. **Riktlinjer** — Övriga rekommendationer

---

## Session-start Checklist

När du startar arbete med BACOWR:

- [ ] Jag har läst `claude.md` (denna fil)
- [ ] Jag har läst `SYSTEM.md` (om jag ska skriva artiklar)
- [ ] Jag har identifierat arbetssätt (Modus 1: Artiklar eller Modus 2: Utbildning)
- [ ] Jag har tillgång till CSV (för artikeljobb) eller ämne (för utbildning)
- [ ] Jag förstår kontextlänk-konceptet (bryggor, inte dekoration)
- [ ] Jag vet var output ska sparas

---

## Quick Reference

| Vill göra | Kommando/Fil |
|-----------|-------------|
| Skriv artikel | Läs SYSTEM.md → Kör jobb → Spara articles/job_NN.md |
| Analysera publisher | `python pipeline.py publisher DOMAIN` |
| Analysera target | `python pipeline.py target URL` |
| Beräkna distans | `python pipeline.py distance --pub-topics ... --tgt-keywords ... --anchor ...` |
| Skapa utbildningsmaterial | Referera SYSTEM.md sektion 3 (Kärnlogiken) + ge exempel |
| Batch-körning | Loop med `claude --background` |
| Rename + DOCX | `python rename_and_convert.py --csv ...` |

---

---

## Veckoplanering — Status (Vecka 4-5 2026)

### ✅ KLART

| Prio | Uppgift | Status | Leverabler |
|------|---------|--------|------------|
| P1 | 30 st Typ 1 texter färdiga och kvalitetssäkrade | Klart | Robin hanterar typ 1 framåt |
| P2 | Utbildningtext - Planering av ankare och målsidor | Klart | `guides/*.md` (7 filer) + `guides/docx/` |
| P2 | Punktlista: Utbildningsmoment för content framåt | Klart | `guides/utbildningsmoment.md` + `utbildningsmoment-punktlista.md` |

### ⚠️ ÅTERSTÅR

| Prio | Uppgift | Notering | Idéer |
|------|---------|----------|-------|
| P3 | Robins uppgifter framåt | Koppla till kundvärde/försäljning | Se sektion nedan |
| P3 | Fortsätta utvecklingen av bulkleveranser | Om tid finns | Se sektion nedan |

---

## Idéer: Robins Uppgifter Framåt

*Möjliga uppgifter kopplade till kundvärde och försäljning:*

### 1. Länkschema-verktyg
- **Vad**: Ett verktyg/rapport som automatiskt genererar länkschema för kund
- **Input**: Kundens målsidor + tillgängliga publishers
- **Output**: Prioriterad matris med bästa publisher-target-kombinationer
- **Kundvärde**: Strategisk översikt, visar professionalism

### 2. Entity Coverage Analys
- **Vad**: Analysera vilka entiteter som täcks i en batch, identifiera gap
- **Input**: Lista över skrivna artiklar
- **Output**: Heatmap/rapport: "Dessa entiteter är täckta, dessa saknas"
- **Kundvärde**: Visar strategiskt tänkande, ej bara volym

### 3. Publisher Profil-databas
- **Vad**: Bygga en databas över publishers med ämnesområde, gap-analys, historik
- **Input**: Publisher-domäner
- **Output**: Återanvändbar profil per publisher
- **Kundvärde**: Snabbare leverans, mer träffsäker planering

### 4. Konkurrentrapporter
- **Vad**: Analysera kundens konkurrenter och deras länkprofil
- **Input**: Kundens domän + konkurrenters domäner
- **Output**: Rapport med insikter om gap och möjligheter
- **Kundvärde**: Säljargument, visar research-djup

### 5. QA-dashboard
- **Vad**: Aggregera QA-resultat över tid för att visa kvalitetsutveckling
- **Input**: QA-tabeller från artiklar
- **Output**: Dashboard/rapport: "Snitt-score över tid, problemområden"
- **Kundvärde**: Visar kvalitetsförbättring, bygger förtroende

### 6. ROI-uppföljning
- **Vad**: Koppla artiklar till SEO-resultat efter 3-6 månader
- **Input**: Artikeldata + ranking-data
- **Output**: Rapport: "Artikel X gav Y% ranking-ökning"
- **Kundvärde**: Bevisar effekt, stödjer merförsäljning

---

## Idéer: Bulkleveranser (Batch-utveckling)

*Möjliga förbättringar av batch-funktionen:*

### Fas 1: Grundläggande Batch-pipeline
- Automatisk CSV-inläsning av 10-50 jobb
- Parallell preflight-analys
- QA-aggregering per batch

### Fas 2: Smart Fördelning
- Automatisk fördelning av målsidor (ej alla till samma)
- Ankartext-variation per målsida
- Entity-balansering över batch

### Fas 3: Dupliceringshantering
- Spåra använda kontextlänkar per publisher
- Varna vid duplicering
- Föreslå alternativa kontextlänkar

### Fas 4: Kvalitetsautomatisering
- Automatisk QA-körning per artikel
- Flagga artiklar som behöver revision
- Generera batch-rapport

### Implementation (om tid finns)
```bash
# Exempel på framtida batch-kommando
python batch_runner.py \
  --csv orders/januari-batch.csv \
  --parallel 10 \
  --qa-threshold 0.8 \
  --output-report batch_report.md
```

---

## Nästa Session

Vid nästa session, överväg att:

1. **Finlir på guides/** — Granska och polera utbildningsmaterialet
2. **Skapa fil för "Robins uppgifter"** — Om beslut fattas om vad som ska prioriteras
3. **Batch-script** — Om tid finns för utveckling
4. **Leverera utbildningsmaterial** — Dela guides/ med content-teamet

---

**System**: BACOWR v5.6
**Specifikation**: 2026-01-29 (uppdaterad 2026-02-03)
**Användningsområden**: Artikelproduktion + Utbildningsmaterial om länkstrategi

*För tekniska detaljer, se AGENT_INSTALLATION.md*
*För skrivregler, se SYSTEM.md*
*För crash recovery, se INIT.md*
*För utbildningsmaterial, se guides/*
