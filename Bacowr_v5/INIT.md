# BACOWR v5.6 — Crash Recovery / Session Init

> Las denna fil FORST om du tar over sessionen.

---

## Systemet

BACOWR v5.6 ar en artikelgenereringspipeline som tar en godtycklig CSV-jobblista och producerar SEO-artiklar med ankarlank, trustlankar och kvalitetskontroll.

**Systemet ar generiskt.** Det ar inte last till en specifik jobblista.

---

## Filstruktur

```
gpt-system-teknisk-dokumentation/
  v5/
    SYSTEM.md              # Instruktioner for artikelgenerering (v5.6)
    README.md              # Snabbstart, pipeline-oversikt
    AGENT_INSTALLATION.md  # Komplett installationsguide for ny agent/batch
    INIT.md                # DENNA FIL
    models.py              # Datamodeller (JobSpec, Preflight, VerifiedSource, etc.)
    pipeline.py            # CSV -> preflight -> artikelprompt
    rename_and_convert.py  # Rename + DOCX (generisk, laser CSV)
    convert_to_docx.py     # Enkel markdown -> DOCX (Pandoc)
    requirements.txt       # Python-beroenden

    articles/              # Output: genererade artiklar
    docx_export/           # Output: DOCX-versioner
    preflight/             # Output: semantisk analys (JSON)
    prompts/               # Output: artikelprompts
```

## CSV-format

Vilken fil som helst med dessa kolumner:

```csv
job_number,publication_domain,target_page,anchor_text
```

## Vilka filer styr vad

| Fil | Roll |
|-----|------|
| `SYSTEM.md` | Alla regler: skrivstil, kontextlankar, ankarlank, QA-tabell, forbjudna fraser |
| CSV-filen | Input-data: publisher, target_url, anchor_text per jobb |
| `models.py` | Type-safe datastrukturer for pipelinen |
| `pipeline.py` | Automatiserad preflight (semantisk distans, bridge-strategi) |
| `rename_and_convert.py` | Rename artiklar + DOCX-export (laser CSV for mappning) |

## Hur man kor ett nytt jobb steg for steg

1. Las `SYSTEM.md` i sin helhet
2. Las raden fran CSV:en for ditt jobb (publisher_domain, target_url, anchor_text)
3. Analysera publisher-domanen (amnesomrade, malgrupp)
4. Analysera target-sidan (metadata, sokord, entiteter)
5. Bestam semantisk distans: hur langt ar publisher fran target?
6. Sok kontextlankar med WebSearch — hitta kallor som BINDER publisher och target
7. Hamta varje kandidat-URL med WebFetch, verifiera HTTP 200, extrahera fakta
8. Formulera artikelns TES — en mening som hela texten driver
9. Skriv artikeln (900+ ord, 1 ankarlank, 1-2 trustlankar)
10. Generera kvalitetskontrolltabell
11. Spara som `v5/articles/job_NN.md`

## Hur man kor en batch

```bash
# Preflight (valfritt)
python pipeline.py run --csv path/to/jobs.csv

# Artiklar — parallella agenter
for i in $(seq 1 25); do
  claude --background "Las v5/SYSTEM.md. Kor jobb $i fran CSVFIL. Spara som v5/articles/job_$(printf '%02d' $i).md"
done

# Rename + DOCX
python rename_and_convert.py --csv path/to/jobs.csv
```

Se `AGENT_INSTALLATION.md` for komplett guide med felsokningshjlp.

## Tidigare batchar

### Batch 1 (2026-01-29): 30 jobb

CSV: `job_list - Blad1.csv` (i parent-mappen)
Status: Alla 30 jobb APPROVED. 60 .md + 30 .docx i articles/ och docx_export/.
