USER MANUAL — Topical Authority Autopilot (TAA)

Version: 1.0.0
Mode: GPT-Integrated
Scope: Full SEO Operations Framework (11 skills)
Last Updated: 2025-12-25

🧩 1. Vad TAA är

Topical Authority Autopilot (TAA) är ett komplett SEO-operationssystem integrerat direkt i GPT-miljön.
Det kombinerar kunskapsbas, verktyg och procedurer för att bygga, optimera och övervaka hela ämnesområden — från seed-topic till leverans.

Det fungerar som en LLM-inbäddad plattform, inte bara en prompt:

Du kan köra varje modul som ett kommandon.

Alla outputs (CSV, JSON, Markdown) simuleras deterministiskt.

Inga nätanrop krävs om du inte explicit ber om det.

⚙️ 2. Arkitekturöversikt
11 interna moduler (skills)
FAS	MODUL	FUNKTION
Ingest	first-party-ingest	Samlar GA4, GSC, loggar → entitetsdata
Crawl	render-crawler	Renderar och auditerar sidor tekniskt
Knowledge	entity-reconciler	Bygger E-E-A-T-graf, länkar till Wikidata
Competitive	competitive-modeler	Jämför topical coverage vs konkurrenter
Forecast	impact-forecaster	ROI-modell, prio av backlog
Links	link-graph-analytics	Intern länkflödes- och entropianalys
Quality	quality-harness	Factuality, depth & E-E-A-T-score
Programmatic	programmatic-factory	Skapar parametisk SEO-content
Schema	schema-compiler	JSON-LD-validering och feature readiness
Monitoring	monitoring-agent	Diffar förändringar, larmar vid regression
Delivery	delivery-devops	Export, publicering och rollback
🧠 3. Hur du använder TAA i GPT

TAA svarar på kommandolika prompts — du skriver som om du använde ett CLI, men får resultat direkt i chatten.

🪄 Bas-syntax
Kommando	Funktion
taa plan --topic "elbilsladdning"	Kör hela topical pipeline (planering, kluster, briefs)
taa run --skills [first-party-ingest, impact-forecaster]	Kör utvalda moduler sekventiellt
taa skill --name schema-compiler	Visa eller kör specifik modul
taa diff --latest	Kör Monitoring Agent mellan senaste runs
taa deploy --target wordpress	Simulera leverans via Delivery DevOps

Varje körning returnerar artefakter i simulerat filformat (/out/...) som du kan kopiera ut i JSON, CSV, YAML eller Markdown.

🧰 4. Outputformat

Du kan be TAA att leverera resultat i något av följande format:

Format	Syntaxexempel	Användning
Markdown	taa skill --name competitive-modeler --format md	Mänskligläsbara rapporter
JSON	taa run --skills [impact-forecaster] --format json	Maskinläsbart, lätt att exportera
CSV	taa run --skills [first-party-ingest] --format csv	Excel- eller BI-import
YAML	taa run --skills [schema-compiler] --format yaml	Config eller validering
🚀 5. Snabbstart
Steg 1 — Planera ett ämne
taa plan --topic "batterilagring"


✅ Producerar:

knowledge_graph.json

topic_clusters.json

content_plan.csv

internal_linking.md

briefs/*.md

Steg 2 — Lägg till crawl och entiteter
taa run --skills [render-crawler, entity-reconciler]


✅ Ger teknisk audit + E-E-A-T-entiteter.

Steg 3 — Prognos och prio
taa run --skills [first-party-ingest, impact-forecaster]


✅ Ger ROI-baserad backlog (backlog_prioritized.csv).

Steg 4 — Schema + kvalitetsgrindar
taa run --skills [schema-compiler, quality-harness]

Steg 5 — Deployment och diff-monitoring
taa run --skills [delivery-devops, monitoring-agent]

🔄 6. Typiska arbetsflöden
🧩 A. Bygg nytt topical område

taa plan --topic "ämne"

taa run --skills [entity-reconciler, competitive-modeler, impact-forecaster]

Exportera briefs, börja produktion.

🧩 B. Drift/uppföljning

taa run --skills [first-party-ingest, monitoring-agent]

Få diff_report.md och alerts.json.

🧩 C. Tekniskt fokus

taa run --skills [render-crawler, schema-compiler, link-graph-analytics]

Validera indexering, schema, internlänkar.

🧮 7. Artifact-läsning

Varje modul lämnar strukturerade filer i ett logiskt filsystem:

Modul	Typiska filer	Användning
first-party-ingest	entity_metrics.parquet, cannibalization.json	Se entitets-ROI och kanibalisering
impact-forecaster	backlog_prioritized.csv, assumptions.yaml	Prioritering efter ROI
schema-compiler	jsonld/*.json, validation_report.md	Schema readiness
monitoring-agent	alerts.json, diff_report.md	Regressioner och varningar

GPT simulerar dessa som block — du kan be:

“Visa out/forecast/backlog_prioritized.csv”
så får du en tabell direkt.

🧩 8. Hur du kombinerar moduler

Du kan skapa kedjor av moduler som speglar verkliga pipelines:

taa run --skills [first-party-ingest, entity-reconciler, impact-forecaster, delivery-devops]


Eller skapa specialflöden:

taa run --skills [quality-harness, programmatic-factory]


Varje modul hämtar automatiskt rätt data från tidigare steg (simulerat i GPT).

📖 9. Inspektera en modul

För att lära dig vad en modul gör:

taa skill --name link-graph-analytics


Det visar hela .md-specen för modulen — 11 sektioner (Purpose → Integration).
Du kan även be:

taa skill --name link-graph-analytics --summarize


för en kortfattad översikt.

🔍 10. Generera rapporter & analyser

Topic gap report
taa run --skills [competitive-modeler] --topic "solenergi"

Internal link decay audit
taa run --skills [link-graph-analytics]

Schema validation summary
taa run --skills [schema-compiler]

Forecast summary table
taa run --skills [impact-forecaster] --format table

🧠 11. Förstå determinism

Allt i TAA är deterministiskt:

Samma inputs → samma outputs.

Det betyder att:

Versionerade .md-skills fungerar som code contracts.

Inga randomiseringar används (t.ex. för prioritering).

Resultat kan reproduceras, verifieras och granskas.

🔒 12. Offline/Online-läge
Läge	Förklaring
Offline (standard)	GPT kör alla regler och heuristiker lokalt; inga nätanrop.
Online (opt-in)	Vid behov kan du be GPT att “aktivera online-enrichment” för Wikidata, SERP, GSC.

Exempel:

taa run --skills [entity-reconciler] --mode online

🧱 13. Utöka TAA

Du kan skapa egna moduler direkt här:

taa skill new --name "local-expertise-analyzer" --based-on quality-harness


GPT genererar då ett .md-skelett (alla 11 sektioner) så du kan modifiera det.
Det registreras virtuellt i index.json.

🧩 14. Snabbreferens för kommandon
Kommando	Beskrivning
taa plan	Kör full topical pipeline
taa run	Kör valda moduler
taa skill	Visa, kör eller skapa modul
taa diff	Jämför körningar
taa deploy	Simulera leverans
taa kit build	Generera hela knowledge base (alla .md)
taa kit zip	Generera ZIP-paket med alla filer
taa help	Visa denna manual
🧰 15. Tips & best practices

Använd 3–4 moduler åt gången för snabb återkoppling.

Kör monitoring-agent efter varje större iteration.

Be alltid om format (--format table/json) för att få strukturerad data.

Spara outputs regelbundet (kopiera till ditt repo eller drive).

Använd GPT:s kodblock som artefakt-simulatorer — varje block motsvarar en fil i /out/.

🧩 16. Exempel på promptmönster

Strategiskt:

“taa plan --topic 'cybersäkerhet' → skapa 5 huvudkluster med entiteter, subtopics och prioritet.”

Analytiskt:

“taa run --skills [competitive-modeler] --topic 'solpaneler' --format table”

Tekniskt:

“taa skill --name render-crawler --simulate run på domain.com”

Operativt:

“taa run --skills [impact-forecaster, delivery-devops] --mode offline --format json”

🧩 17. Sammanfattning

TAA i GPT är en självständig SEO-autopilot:

💡 Från ämnesfrö till publicerad plan.

🔁 Från data → entiteter → innehåll → distribution.

🧱 Varje steg definierat, spårbart, och integrerat.

⚙️ Körbart och dokumenterat direkt i GPT — utan externa verktyg.

Kort sagt:
Du har nu hela Topical Authority-verktygslådan — redo att köra, analysera och bygga ut direkt här.