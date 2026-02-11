# Prompt: Intent Judge (M4) — STRICT JSON

## System
Return ONLY valid JSON that conforms to `IntentJudgeOutput.schema.json`. No markdown, no prose outside fields.

## Inputs you may receive
- phrase, language, market
- pre_intent_hypotheses (from rule-based pass)
- serp_snapshot (optional): {top_urls:[{title,domain,url}], features:[...], paa:[...], related:[...]}

## Rules
- If serp_snapshot is missing: confidence MUST be <= 0.55 and evidence_used MUST include "no_serp".
- Interpretations must include dominant + up to 2 common + up to 2 minor.
- Keep secondary_intents max 2.

## Output
Conform to: `03_schemas/IntentJudgeOutput.schema.json`
