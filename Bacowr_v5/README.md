# BACOWR v5.6 — Konsoliderad Artikelpipeline

6 karnfiler + 2 hjalpfiler. Tar vilken jobblista (CSV) som helst.

## Filer

| Fil | Syfte |
|-----|-------|
| `SYSTEM.md` | Alla artikelregler (BACOWR + SKILL + QA + kallverifiering) |
| `pipeline.py` | CSV → preflight → artikelprompt |
| `models.py` | Datamodeller |
| `rename_and_convert.py` | Rename + DOCX (laser CSV, generisk) |
| `convert_to_docx.py` | Enkel markdown → DOCX (Pandoc) |
| `requirements.txt` | Python-beroenden |
| `INIT.md` | Crash recovery / sessionsoversikt |
| `AGENT_INSTALLATION.md` | Komplett installationsguide for ny agent |
| `README.md` | Detta dokument |

## Snabbstart

```bash
# Installera beroenden
pip install -r requirements.txt

# Kor preflight + prompts for alla jobb i en CSV
python pipeline.py run --csv path/to/jobs.csv

# Enskilt jobb
python pipeline.py run --csv path/to/jobs.csv --job 14

# Intervall
python pipeline.py run --csv path/to/jobs.csv --start 1 --end 10
```

## CSV-format (kraven)

```csv
job_number,publication_domain,target_page,anchor_text
1,sportligan.se,https://happycasino.se/,Happy Casino
2,villanytt.se,https://www.rusta.com/sv/mattor,mattor
```

4 kolumner, exakta header-namn. Filen kan heta vad som helst.

## Artikelgenerering (Claude Code)

```bash
# Enskilt jobb — interaktivt
# Be agenten: "Las v5/SYSTEM.md. Kor jobb N fran min_lista.csv. Spara som v5/articles/job_NN.md"

# Batch — parallella bakgrundsagenter
for i in $(seq 1 25); do
  claude --background "Las v5/SYSTEM.md. Kor jobb $i fran min_lista.csv. Spara som v5/articles/job_$(printf '%02d' $i).md"
done
```

## Rename + DOCX

```bash
# Generisk — laser CSV for namnmappning
python rename_and_convert.py --csv path/to/jobs.csv
python rename_and_convert.py --csv path/to/jobs.csv --job 14
```

## Output

```
v5/
├── preflight/           # JSON — semantisk analys per jobb
├── prompts/             # Markdown — artikelprompts
├── articles/            # Genererade artiklar (.md)
├── docx_export/         # DOCX-versioner
└── all_preflights.json  # Kombinerad data
```

## Pipeline-steg

1. **CSV → JobSpec** — Laser jobb (publisher, target, anchor)
2. **Publisher-analys** — Domannamn + homepage-meta → topics
3. **Target-analys** — Sidmetadata, keywords, Schema.org
4. **Semantisk distans** — Embedding-baserad similarity
5. **Bridge-generering** — Variabelgifte publisher ↔ target
6. **Kallverifiering** — WebSearch + WebFetch = verifierade djuplinkar
7. **Prompt-generering** — Komplett artikelinstruktion
8. **Artikelskrivning** — Claude-agent med SYSTEM.md som instruktion
9. **Rename + DOCX** — rename_and_convert.py

## Forutsattningar

- Python 3.10+
- Pandoc (for DOCX-export, valfritt)
- `python-docx` (for rename_and_convert.py)
- CSV med kolumnerna: `job_number`, `publication_domain`, `target_page`, `anchor_text`

## Dokumentation

- **Ny agent?** Las `AGENT_INSTALLATION.md`
- **Crash recovery?** Las `INIT.md`
- **Skrivregler?** Las `SYSTEM.md`
