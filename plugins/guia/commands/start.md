---
description: START — begin work on a `Planejada` or `Backlog` task (status → `Em desenvolvimento`). Assumes triage is done (kind already decided); use `promote` when kind still needs deciding. Options: `--note "<starting note>"`. To resume from `Bloqueada` use `unblock`; to create a fresh task use `feature`/`bug`/`chore`.
---

# Start

**Start work on a Planejada task (or directly from the Backlog).** Moves status to `Em desenvolvimento`. Assumes triage (kind = feature/bug/chore) is done — if you still need to decide the kind, use `$promote`.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
start <D-NNN> [--note "Starting now because..."]
```

Distinct from:
- `$promote <B-NNN>`: triage a backlog item deciding kind and plan before starting.
- `$plan`: mark as triaged without starting.
- `$feature/$bug/$chore` (new tasks): create a fresh task already `Em desenvolvimento`.

Accepts transition from `Backlog` (shortcut that skips `Planejada`) or `Planejada`. Fails if the task is already `Em desenvolvimento`, in a terminal state (`Validada`, `Finalizada`, `Cancelada`), or `Bloqueada` (use `$unblock`).

Tasks promoted from `Backlog` enter `.guia/DEMANDAS.md`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
