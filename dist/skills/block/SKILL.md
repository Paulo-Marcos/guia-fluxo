---
name: block
description: PAUSE an in-flight task — preserves WIP and moves status to `Bloqueada`. Use when the task will return: waiting on a decision, external dependency, priority swap. Required: `--reason "<motive>"` (recorded in `task.blocks[]`). To resume use `unblock`; for terminal close use `cancel`; for handoff to validation use `ready`.
---

# Block

**Pause the current task with a mandatory reason.** Moves status to `Bloqueada`, preserves the WIP, and keeps the entry in `FEATURES.md`. Use to stop temporarily: external dependency, waiting on a decision, priority swap. Distinct from `cancel` (terminal, does not return) and `finish` (validated and closed).

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
block <D-NNN> --reason "Why pausing"
```

`--reason` is **required** (recorded in `task.blocks[]` for blocked-time auditing).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already in `Bloqueada`.

To resume, use the `unblock` verb (`unblock <D-NNN>`).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
