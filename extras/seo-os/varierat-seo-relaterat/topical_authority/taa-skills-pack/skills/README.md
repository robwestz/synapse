# Topical Authority Autopilot — Knowledge Base (v1.0.0)

Modulärt kompetensbibliotek (11 skills) som gör TAA till ett fullstack, entitetsdrivet SEO-operations-ramverk. Offline-först, deterministiskt, och artefakt-centrerat.

## Arkitektur (översikt)
Ingest → Knowledge → Competitive/Forecast → Quality/Automation → Monitoring/Delivery

## Körmönster (CLI designförslag)
- `taa kit build` — generera alla skills-filer
- `taa skill --name schema-compiler` — visa/kör en modul
- `taa run --skills [first-party-ingest, impact-forecaster]`
- `taa diff --latest` — kör Monitoring Agent
- `taa deploy --target wordpress` — Delivery & DevOps

Se `index.json` för beroenden och artefakter.