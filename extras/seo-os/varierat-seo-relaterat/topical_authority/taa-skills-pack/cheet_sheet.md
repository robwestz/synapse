TAA CHEAT SHEET (v1.0.0)

Topical Authority Autopilot — GPT Edition
Entity-first, deterministic, fully modular SEO automation system.
Allt kan köras direkt i GPT.

🧩 Core Concepts
Element	Förklaring
Skill	En modul med tydligt input/output-kontrakt (t.ex. schema-compiler).
Pipeline	Sekvens av skills som bearbetar ett ämne.
Artifact	Fil eller strukturerad output som varje skill producerar.
Determinism	Samma input → samma output (offline-läge).
Mode	offline (standard) eller online (opt-in enrichment).
🧠 Skill Ecosystem
FAS	SKILL	FUNKTION / OUTPUT
Ingest	first-party-ingest	GA4, GSC, loggar → entity_metrics.parquet
Crawl	render-crawler	Indexering & schema audit → audit_issues.md
Knowledge	entity-reconciler	E-E-A-T + Wikidata → reconciled_entities.json
Competitive	competitive-modeler	Gap vs konkurrenter → coverage_matrix.csv
Forecast	impact-forecaster	ROI-baserad prio → backlog_prioritized.csv
Links	link-graph-analytics	Authority flow → graph_metrics.csv
Quality	quality-harness	Factuality, depth → quality_report.csv
Programmatic	programmatic-factory	Parametrisk contentgen → pages/*.html
Schema	schema-compiler	JSON-LD validation → validation_report.md
Monitoring	monitoring-agent	Diff + larm → alerts.json, diff_report.md
Delivery	delivery-devops	Deploy/rollback → manifest.json, deploy_log
⚙️ Core Commands (GPT Context)
Kommando	Funktion
taa plan --topic "x"	Kör full topical pipeline
taa run --skills [a,b,c]	Kör valda moduler
taa skill --name y	Visa/kör modul
taa diff --latest	Jämför två körningar
taa deploy --target cms	Simulera leverans
taa kit build	Regenerera skillsbiblioteket
taa kit zip	Skapa ZIP med alla filer
taa help	Visa full manual
🧮 Output Formats
Format	Syntax	Exempel
Markdown	--format md	För rapporter
JSON	--format json	För maskinläsning
CSV	--format csv	För BI / Sheets
YAML	--format yaml	För config/export
🚀 Common Workflows
🔹 Topical Launch
taa plan --topic "elbilsladdning"


→ Knowledge Graph + Clusters + Briefs

🔹 Forecast & ROI
taa run --skills [first-party-ingest, impact-forecaster]


→ Prioritized backlog

🔹 Schema & Validation
taa run --skills [schema-compiler, quality-harness]


→ JSON-LD + QA reports

🔹 Monitoring
taa run --skills [monitoring-agent]


→ alerts.json, diff_report.md

🔁 Typical Pipelines
first-party-ingest → competitive-modeler → impact-forecaster → delivery-devops
render-crawler → link-graph-analytics → monitoring-agent
entity-reconciler → schema-compiler → quality-harness → delivery-devops

🧩 Artifact Reference
Output	Producer	Description
knowledge_graph.json	plan	Entitetsrelationer
topic_clusters.json	plan	Hub-spoke struktur
content_plan.csv	plan	Publiceringsplan
backlog_prioritized.csv	forecaster	ROI-baserad backlog
validation_report.md	schema	Schema status
diff_report.md	monitoring	Diff mellan körningar
manifest.json	delivery	Deploy-logg
🧠 Prompt Examples
Typ	Prompt
Strategisk	taa plan --topic "cybersäkerhet" --lang sv
Analytisk	taa run --skills [competitive-modeler] --format table
Teknisk	taa skill --name render-crawler --simulate run
Drift	taa run --skills [monitoring-agent, delivery-devops]
📘 Quick Best Practices

✅ Kör 3–4 moduler åt gången för feedback
✅ Kör monitoring-agent efter större iterationer
✅ Använd --format json vid export till BI
✅ Dokumentera antaganden i assumptions.yaml
✅ Spara outputs i ditt repo för versionsspårning

🧩 Determinism Check
taa run --skills [impact-forecaster]
taa run --skills [impact-forecaster]
# Outputs ska vara identiska

🧱 Extend TAA
taa skill new --name "local-expertise-analyzer" --based-on quality-harness


→ Skapar nytt .md-skelett (11 sektioner) registrerat i index.json.

🧾 Contact & Maintenance

Uppdatera skills/index.json vid nya moduler.

Regenerera ZIP via taa kit zip.

Läs OPERATIONS.md för full driftinstruktion.

Offline först — aktivera online endast vid behov.