---
description: RESUME a paused task — moves status from `Bloqueada` back to `Em desenvolvimento`. Inverse of `block`. Options: `--note "<what unblocked>"`. Fails if the task wasn't `Bloqueada` (preserves flow states).
---

# Unblock

**Resume a paused task.** Moves status from `Bloqueada` back to `Em desenvolvimento`. Use after `block` once the dependency/decision blocking the work has been resolved.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
unblock <D-NNN> [--note "What unblocked it"]
```

`--note` is optional — useful when it is worth recording what unblocked it (decision made, dependency resolved).

Fails if the task was not in `Bloqueada` (preserves the flow states).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
