---
name: backlog
description: DEFER-AND-PARK skill: never starts implementation. Triggered ONLY by /backlog or "$backlog" with a subcommand (add / list). Saves future ideas to .guia/backlog.json (B-NNN) or lists them. Do NOT use for: starting work now (use $feature for new functionality, $bug for regressions, or $chore for maintenance), or evaluating one specific B-NNN to convert it (use $promote).
---

# Backlog

Manage parked work without starting implementation. `backlog add` creates a `D-NNN` task with `status=Backlog`. `backlog list` shows all parked items (new D-NNN + legacy B-NNN). `backlog promote` delegates to the `/promote` flow.

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

If the user provided a title, run:

```powershell
.\core\bin\guia.ps1 backlog add "<title>" --context "<context>"
```

To list parked work:

```powershell
.\core\bin\guia.ps1 backlog list
```

To promote a backlog item:

```powershell
.\core\bin\guia.ps1 backlog promote B-001
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py backlog add|list|promote ...`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
