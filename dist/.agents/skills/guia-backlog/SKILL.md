---
name: guia-backlog
description: DEFER-AND-PARK skill: never starts implementation. Triggered ONLY by /backlog or "$backlog" with a subcommand (add / list). Saves future ideas to .guia/backlog.json (B-NNN) or lists them. Do NOT use for: starting work now (use $feature for new functionality, $bug for regressions, or $chore for maintenance), or evaluating one specific B-NNN to convert it (use $promote).
---

# Backlog Shim

Manage parked work. `backlog add` creates a `D-NNN` task with `status=Backlog` (not started). `backlog list` shows all parked items (new D-NNN + legacy B-NNN). `backlog promote` delegates to the `/promote` flow.

## Title vs Context

When the human asks in loose phrasing, **synthesize** — do not pass the raw sentence to the CLI.

- `<title>`: short imperative, 5–8 words, ≤60 chars. Captures the *what*. Title is what shows in `NOME DO CHAT` and in task lists.
- `<context>`: full motivation, scenario, success criteria. Captures the *why*. Multi-line allowed. Goes into `task.context`, `FEATURES.md`, and search.

Example:

> Human: "queria que o /finish mostrasse o tempo total da task"
>
> → title:   `Show total task time on /finish`
> → context: `User wants /finish to print elapsed time since task creation so they can see how long the work took without opening JSON.`

If the human-provided phrasing already reads as an imperative under 60 chars, use it as-is. Synthesis is for loose/long phrasings, not a mandatory rewrite.

Call the core process script:

```powershell
.\core\bin\guia.ps1 backlog add "<title>" --context "<context>"
.\core\bin\guia.ps1 backlog list
.\core\bin\guia.ps1 backlog promote B-001
```

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

**Do not start implementation.** Backlog is the defer-and-park surface. To begin work on a parked item later, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
