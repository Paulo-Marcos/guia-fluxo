---
description: "PRIMARY TRIGGER — create a new `D-NNN` bug task for a regression, defect, or incorrect behavior. Options: `--context \"<symptom + impact>\"`, `--origin \"<source>\"`, `--status backlog|planned|in-development` (default `in-development`). For new capabilities use `feature`; for maintenance without behavior change use `chore`."
---

# Bug

Create a bug task before editing code. Use for a regression, a defect, or any incorrect behavior that needs investigation and fix.

## Title vs Context

When the human asks in loose phrasing, **synthesize** — do not pass the raw sentence to the CLI.

- `<title>`: short imperative, 5–8 words, ≤60 chars. Captures the *what*. Title is what shows in `NOME DA DEMANDA` and in task lists.
- `<context>`: full motivation, scenario, success criteria. Captures the *why*. Multi-line allowed. Goes into `task.context`, `.guia/DEMANDAS.md`, and search.

Example:

> Human: "queria que o /finish mostrasse o tempo total da task"
>
> → title:   `Show total task time on /finish`
> → context: `User wants /finish to print elapsed time since task creation so they can see how long the work took without opening JSON.`

If the human-provided phrasing already reads as an imperative under 60 chars, use it as-is. Synthesis is for loose/long phrasings, not a mandatory rewrite.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
bug "<title>" --context "<observed symptom + impact>"
```

Useful flags:
- `--context "<symptom + impact>"` — observed behavior vs expected, who is affected.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` if not triaged, `planned` if planned but not now.
- `--origin "<source>"` — alternate origin.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Name the chat and record it (D-157)** — when this chat starts or resumes work on the demand, so the developer can come back to it when the queue returns it or leaves it pending:
   - Run `chat <D-NNN>`: it prints `NOME DO CHAT: ...`, a stable name without the status tag.
   - **Chat dedicated to this demand:** rename the session to that name — the session-title tool when this build has one, `mark_chapter` (`mcp__ccd_session__mark_chapter`, also places a divider + ToC entry), and/or `/rename <name>` — then record it: `chat <D-NNN> --title "<name>"`.
   - **Chat that already holds other demandas:** do not rename it to this demand (it would mislead); record the name the chat already has (the demand it started with): `chat <D-NNN> --title "<that name>"`.
   - **Always show the chat name to the developer**, even when renaming is not available, so it can be saved. The queue, `next` and `status --all` cite it ("volte ao chat: ...").
4. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
5. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

## File locks

Before editing files, honor `.guia/locks/registry.yaml`. If a target file is locked:

1. **Stop** before the edit.
2. **Explain to the developer**, in this order:
   - The lock id and which functionality it protects.
   - Why the planned edit is needed.
   - Expected impact (what changes, who notices).
   - Regression risk (what could break that is currently working).
   - Alternatives (route the change through a different file, scope reduction, etc.).
3. **Ask** for explicit authorization to proceed (or to unlock).
4. Only after the developer authorizes, edit — or use `python core/lock/check-lock.py unlock <id>` if the developer asks for the lock to be removed.

Never bypass a lock silently. The hook at commit time will reject the commit anyway, and the developer loses trust if the agent treats locks as advisory.

## Regression test before the fix

Every bug is fixed in this order — the test is the proof that the bug existed and is gone:

1. **Write the test first**, reproducing the reported behavior with synthetic data. Run it and **see it fail** for the reason in the report. A test that passes before the fix proves nothing.
2. **Fix**, then see the same test pass. Keep the test: it guards against the bug coming back.
3. **Only the fix.** No drive-by refactor, no speculative abstraction, no weakened or deleted test, no TODO left behind — those are separate tasks.
4. If a test is genuinely impossible (pure visual glitch, timing on real hardware), say so in `--validation` and describe the manual check that replaces it.

Record the before/after in `ready --validation` (e.g. "test X failed on HEAD before the fix, passes after").

Then continue with the investigation and fix.
