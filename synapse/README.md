# Synapse Scaffold (Agents + Skills)

Detta är ett scaffold-lager för:
- `agents/` (agentkontrakt och basimplementation)
- `skills/` (testbara beräkningsmoduler)
- `kernel/skills.ts` + `kernel/skill_runner.ts` (registry + exekvering)

## Syfte
Ge en stabil startpunkt för ticket-arbete enligt `SYNAPSE_CURSOR_SPEC.md`, utan att behöva tolka struktur från scratch efter agent/IDE-avbrott.

## Viktigt
- Flera implementationer är medvetet markerade som placeholders.
- Full produktlogik byggs ticket-för-ticket enligt spec.
- Kontraktsändringar måste loggas i `.planning/DECISIONS_LOG.md` innan implementation.
