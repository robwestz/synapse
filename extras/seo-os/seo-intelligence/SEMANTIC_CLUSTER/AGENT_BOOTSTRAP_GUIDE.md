# 🧠 AGENT PERSISTENCE FRAMEWORK v1.0

> **MANDATORY READING** — Every agent MUST read this file at session start.
> This framework prevents context loss and ensures continuous progress across sessions.

---

## THE PROBLEM THIS SOLVES

After ~100-200k tokens, LLMs lose track of:
- What the original mission was
- What has been completed vs. remaining
- Why certain decisions were made
- How to continue coherently

**This framework solves this through enforced documentation and atomic task completion.**

---

## CORE PRINCIPLES

### 1. THE ATOM PRINCIPLE
> **Complete one thing fully before starting another.**

- Every task is broken into **atomic items** (small, completable units)
- An item is either `PENDING`, `IN_PROGRESS`, or `COMPLETE`
- Never leave items half-done — finish or roll back
- When complete, move to next item immediately

### 2. THE CONTRACT PRINCIPLE  
> **If it's not written, it didn't happen.**

- All state lives in `BUILD_CONTRACT.json`
- All planning lives in `ROADMAP.md` or `implementation_plan.md`
- All progress lives in `task.md` (checklist format)
- Update these files **during** work, not after

### 3. THE RESUMPTION PRINCIPLE
> **Any agent should be able to continue from any point.**

- State files must be self-explanatory
- No tribal knowledge — everything documented
- First action of any session: read state, report status, continue

---

## REQUIRED FILES

Every project using this framework MUST have:

| File | Purpose | Format |
|------|---------|--------|
| `BUILD_CONTRACT.json` | Live state tracking | JSON with phases/items/status |
| `ROADMAP.md` | High-level plan | Markdown with phases |
| `task.md` | Active checklist | `[ ]`, `[/]`, `[x]` notation |
| `SPEC.md` or `PRD.md` | The "why" and requirements | Markdown |

---

## BUILD_CONTRACT.json STRUCTURE

```json
{
  "project_name": "Project Name",
  "current_phase": "phase_id",
  "current_item": "item_id",
  
  "phases": {
    "phase_1": {
      "name": "Phase Name",
      "gate": "What must be true to complete this phase",
      "items": [
        {"id": "P1_1", "name": "Task name", "status": "COMPLETE", "file": "path/to/file.py"},
        {"id": "P1_2", "name": "Next task", "status": "IN_PROGRESS", "file": "path/to/other.py"},
        {"id": "P1_3", "name": "Pending task", "status": "PENDING", "file": "path/to/future.py"}
      ]
    }
  },
  
  "files_created": [],
  "last_updated": "ISO timestamp"
}
```

---

## SESSION START PROTOCOL

**Every session MUST begin with:**

```
1. READ BUILD_CONTRACT.json
2. IDENTIFY current_phase and current_item
3. REPORT status to user:
   "Resuming [project]. Phase: [X]. Current item: [Y]. Status: [Z]."
4. IF item is IN_PROGRESS → continue it
   IF item is PENDING → start it
   IF all items COMPLETE → ask for direction
```

---

## TASK EXECUTION PROTOCOL

**For each atomic item:**

```
1. Mark item as IN_PROGRESS in contract
2. Do the work (create/modify files)
3. Verify work is complete
4. Mark item as COMPLETE in contract
5. Add files to files_created list
6. Update task.md checkbox ([/] → [x])
7. Move current_item pointer to next PENDING
8. Repeat
```

---

## TASK.MD FORMAT

```markdown
# Project Task List

## Phase 1: Foundation

- [x] Completed item
- [/] In progress item  
- [ ] Pending item

## Phase 2: Features

- [ ] Future item 1
- [ ] Future item 2
```

**Notation:**
- `[ ]` = Not started
- `[/]` = In progress (custom, widely understood)
- `[x]` = Complete

---

## ATOMIC ITEM RULES

### What makes a good atomic item?
✅ Completable in 1-3 tool calls  
✅ Results in a tangible output (file, function, test)  
✅ Has a clear "done" state  
✅ Can be verified independently  

### What is NOT atomic?
❌ "Build the feature" (too vague)  
❌ "Research options" (no tangible output)  
❌ "Fix bugs" (unbounded)  

### Good examples:
- "Create `user_model.py` with User dataclass"
- "Add `/login` endpoint to `api.py`"
- "Write unit test for `calculate_score()`"

---

## CONTEXT RECOVERY

If you (the agent) feel confused or lost:

```
1. STOP current work
2. READ BUILD_CONTRACT.json completely
3. READ ROADMAP.md or SPEC.md
4. READ last 3 entries in files_created
5. REPORT findings to user
6. ASK for clarification if still unclear
```

---

## PHASE GATES

Each phase has a **gate** — a condition that must be true to proceed.

Examples:
- "All items COMPLETE and API returns 200 on /health"
- "All tests pass and user has approved UI"
- "Database migrations run successfully"

**Do not proceed to next phase until gate is satisfied.**

---

## HANDOFF DOCUMENTATION

When ending a session or switching agents:

```
1. Ensure BUILD_CONTRACT.json is current
2. Ensure task.md reflects true state
3. Add summary comment to ROADMAP.md if needed
4. Leave no IN_PROGRESS items (complete or revert)
```

---

## ANTI-PATTERNS TO AVOID

| ❌ Anti-pattern | ✅ Correct approach |
|----------------|---------------------|
| Starting new work without checking state | Always read contract first |
| Leaving items IN_PROGRESS at session end | Complete or mark PENDING |
| "I'll document later" | Document during work |
| Mega-tasks spanning 10+ tool calls | Break into atomic items |
| Assuming context from conversation | Trust only written files |
| Skipping verification | Always verify before marking complete |

---

## EXAMPLE SESSION

```
Agent: [Reads BUILD_CONTRACT.json]
Agent: "Resuming ProjectX. Phase: core_api. Current item: C3 (Add auth middleware). 
        Status: PENDING. Items C1-C2 complete."
Agent: [Marks C3 as IN_PROGRESS]
Agent: [Creates auth_middleware.py]
Agent: [Tests middleware]
Agent: [Marks C3 as COMPLETE, updates files_created]
Agent: [Moves current_item to C4]
Agent: "C3 complete. Proceeding to C4: Add rate limiting."
```

---

## FRAMEWORK ADOPTION CHECKLIST

To adopt this framework for a new project:

- [ ] Create `BUILD_CONTRACT.json` with phases and items
- [ ] Create `ROADMAP.md` with high-level plan
- [ ] Create `task.md` with checkbox items matching contract
- [ ] Create `SPEC.md` or `PRD.md` with requirements
- [ ] Add this file as `AGENT_BOOTSTRAP.md` in project root
- [ ] First line of user prompt: "Read AGENT_BOOTSTRAP.md first"

---

## TL;DR FOR AGENTS

```
1. READ state files before doing anything
2. WORK on ONE atomic item at a time
3. COMPLETE items fully before moving on
4. UPDATE state files during work, not after
5. NEVER assume context — trust only written files
6. WHEN confused, stop and re-read state
```

---

*Framework version: 1.0 | Created: 2024-12-19*
