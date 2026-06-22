---
name: guia-bug
description: PRIMARY TRIGGER — create a new `D-NNN` bug task for a regression, defect, or incorrect behavior. Options: `--context "<symptom + impact>"`, `--origin "<source>"`, `--status backlog|planned|in-development` (default `in-development`). For new capabilities use `feature`; for maintenance without behavior change use `chore`.
---

# Bug

Create a bug task before editing code. Use for a regression, a defect, or any incorrect behavior that needs investigation and fix.

## Title vs Context

When the human asks in loose phrasing, **synthesize** — do not pass the raw sentence to the CLI.

- `<title>`: short imperative, 5–8 words, ≤60 chars. Captures the *what*. Title is what shows in `NOME DO CHAT` and in task lists.
- `<context>`: full motivation, scenario, success criteria. Captures the *why*. Multi-line allowed. Goes into `task.context`, `.guia/DEMANDAS.md`, and search.

Example:

> Human: "queria que o /finish mostrasse o tempo total da task"
>
> → title:   `Show total task time on /finish`
> → context: `User wants /finish to print elapsed time since task creation so they can see how long the work took without opening JSON.`

If the human-provided phrasing already reads as an imperative under 60 chars, use it as-is. Synthesis is for loose/long phrasings, not a mandatory rewrite.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
bug "<title>" --context "<observed symptom + impact>"
```

Useful flags:
- `--context "<symptom + impact>"` — observed behavior vs expected, who is affected.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` if not triaged, `planned` if planned but not now.
- `--origin "<source>"` — alternate origin.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

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

Then continue with the investigation and fix.
