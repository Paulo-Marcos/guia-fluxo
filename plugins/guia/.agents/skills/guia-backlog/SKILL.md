---
name: guia-backlog
description: DEFER-AND-PARK skill — never starts implementation. Subcommands: `add <title> --context "<why>"` parks an idea (saved to `.guia/tasks.json` with `status=Backlog`); `list` shows all parked items; `promote <id>` delegates to the promote flow. To start work immediately use `feature`/`bug`/`chore`; to evaluate one parked item before converting use `promote`.
---

# Backlog

Manage parked work without starting implementation. `backlog add` creates a `D-NNN` task with `status=Backlog`. `backlog list` shows all parked items. `backlog promote` delegates to the `/promote` flow.

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
backlog add "<title>" --context "<context>"    # if the user provided a title
backlog list                                   # show parked work
backlog promote B-001                          # promote a backlog item
```

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
