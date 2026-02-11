# BACOWR v5.6 — Agentinstallation och batchkorning

> Komplett guide for att installera systemet i en ny Claude Code-session
> och kora artiklar fran godtycklig jobblista.

---

## 1. Forutsattningar

| Krav | Detalj |
|------|--------|
| Claude Code | Med WebSearch + WebFetch aktiverat |
| Python 3.10+ | For pipeline.py (preflight/prompts) |
| Pandoc | For DOCX-export (valfritt) |
| CSV-fil | Med kolumnerna: `job_number`, `publication_domain`, `target_page`, `anchor_text` |

---

## 2. Filstruktur

```
v5/
├── SYSTEM.md                # Alla artikelregler (las FORST)
├── INIT.md                  # Snabb statusoversikt / crash recovery
├── AGENT_INSTALLATION.md    # DENNA FIL
├── README.md                # Snabbstart
├── pipeline.py              # CSV → preflight → artikelprompt
├── models.py                # Datamodeller
├── rename_and_convert.py    # Rename + DOCX-konvertering (generisk)
├── convert_to_docx.py       # Enkel markdown → DOCX
├── requirements.txt         # Python-beroenden
│
├── articles/                # Output: genererade artiklar
├── docx_export/             # Output: DOCX-versioner
├── preflight/               # Output: semantisk analys (JSON)
└── prompts/                 # Output: artikelprompts
```

---

## 3. CSV-format

Filen kan heta vad som helst. Kolumner (exakt dessa headers):

```csv
job_number,publication_domain,target_page,anchor_text
1,sportligan.se,https://happycasino.se/,Happy Casino
2,villanytt.se,https://www.rusta.com/sv/mattor,mattor
```

| Kolumn | Betydelse |
|--------|-----------|
| `job_number` | Unikt heltal (1, 2, 3...) |
| `publication_domain` | Sajten dar artikeln publiceras (t.ex. `sportligan.se`) |
| `target_page` | Kundens URL som ankarlnken pekar till |
| `anchor_text` | Exakt text som blir klickbar i artikeln |

### Sprakdetektering

Systemet detekterar sprak automatiskt:
- `.co.uk`, `.com` med engelska ord i domanen → engelska
- Allt annat → svenska

Om du har blandade sprak: lagg till en kolumn `language` (sv/en) i CSV:en.
Pipeline.py behover da en liten andring i `detect_language()`.

---

## 4. Steg-for-steg: Ny batch

### 4.1 Forberedelse

```bash
# Klona/kopiera v5-mappen till arbetskatalogen
# Placera din CSV nagon tillganglig

# Installera Python-beroenden (for preflight)
pip install -r v5/requirements.txt
```

### 4.2 Kor preflight (valfritt men rekommenderat)

```bash
# Generera semantisk analys + artikelprompts
python v5/pipeline.py run --csv din_jobblista.csv --output v5/

# Enskilt jobb
python v5/pipeline.py run --csv din_jobblista.csv --job 3
```

Output: `v5/preflight/` + `v5/prompts/` — JSON och markdown som hjalper agenten.

### 4.3 Generera artiklar (Claude Code-agenter)

**Enskilt jobb (interaktivt):**

Instruera agenten:
```
Las v5/SYSTEM.md.
Las rad N fran [din CSV].
Analysera publisher och target.
Sok kontextlankar med WebSearch, verifiera med WebFetch.
Skriv artikeln, spara som v5/articles/job_NN.md.
```

**Batch (parallella bakgrundsagenter):**

```bash
# Starta 25 parallella agenter
for i in $(seq 1 25); do
  claude --background "Las v5/SYSTEM.md. Kor jobb $i fran din_jobblista.csv. Spara som v5/articles/job_$(printf '%02d' $i).md"
done

# Vantan, sedan resterande
for i in $(seq 26 50); do
  claude --background "Las v5/SYSTEM.md. Kor jobb $i fran din_jobblista.csv. Spara som v5/articles/job_$(printf '%02d' $i).md"
done
```

**Rate limits:** 25 parallella agenter fungerar. Forvanta nagra retries. Typisk tid: 15-30 min for 25 artiklar.

### 4.4 Rename + DOCX-export

Nar alla artiklar ar klara:

```bash
python v5/rename_and_convert.py --csv din_jobblista.csv --articles v5/articles --docx v5/docx_export
```

Scriptet:
1. Laser varje `job_NN.md`
2. Extraherar rubrik, target-brand och publisher fran CSV:en
3. Skapar `NNN_target_publisher_rubrikslug.md` (kopia)
4. Konverterar till `.docx` i docx_export/

---

## 5. Kvalitetskontroll

Varje artikel har en kvalitetskontrolltabell i slutet. Stickprovskontrollera 5-10 artiklar:

| Kontroll | Var |
|----------|-----|
| Ordantal ≥ 900 | QA-tabellen i artikeln |
| Ankarlank position ord 150-700 | QA-tabellen |
| Trustlankar verifierade | Oppna URL:erna — returnerar de 200? |
| Inga AI-markoerer | Sok efter "I denna artikel", "Sammanfattningsvis", etc. |
| Rod trad | Las texten — driver varje stycke tesen framat? |

---

## 6. Dupliceringsregel (flerga batchar)

Om du kor flera batchar over tid:
- **Samma publisher far inte samma trustlank i tva artiklar.** Kontrollera mot tidigare leveranser.
- **Samma target-brand kan ha flera artiklar** — men pa olika publishers med olika vinklar.

---

## 7. Felsoekning

| Problem | Losning |
|---------|---------|
| WebFetch blockerad | Bakgrundsagenter har ibland begransad WebFetch. Kor interaktivt istallet. |
| Rate limit | Minska parallella agenter till 10-15. |
| CSV hittas inte | Ange fullstandig sokvag med `--csv`. |
| Preflight crashar | Kontrollera att `sentence-transformers` ar installerat. Utan den kor pipelinen med fallback-distans (0.5). |
| DOCX-export misslyckas | Kontrollera att `python-docx` ar installerat (`pip install python-docx`). |
| Artikeln ar for kort | SYSTEM.md kraver 900+ ord. Be agenten forlaanga. |
| Ankarlank i fel position | QA-tabellen visar positionen. Be agenten flytta. |

---

## 8. Anpassa systemet

### Lagga till nya vertikaler

I `pipeline.py`, klassen `SemanticEngine`, utoka `VERTICAL_BRIDGES`:

```python
VERTICAL_BRIDGES = {
    # befintliga...
    ("ny_vertikal", "ny_target"): ["brygkoncept1", "brygkoncept2", "brygkoncept3"],
}
```

### Lagga till nya domantopic-hints

I `pipeline.py`, klassen `PublisherProfiler`, utoka `DOMAIN_MAP`:

```python
DOMAIN_MAP = {
    # befintliga...
    "nytt_domanord": ["topic1", "topic2"],
}
```

### Andra artikelregler

Redigera `v5/SYSTEM.md`. Alla skrivregler, forbjudna fraser, ankarlanksplacering etc. styrs darifran.
