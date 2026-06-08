---
name: status
description: READ-ONLY — show the current active task and the suggested chat title. Optional: `<D-NNN>` to inspect a specific task instead of the current one. Never creates, modifies, advances, or closes a task. To create use `feature`/`bug`/`chore`; for state transitions use `ready`/`finish`/`block`/`unblock`/`cancel`.
---

# Status

Show the current Guia Fluxo task and the suggested chat title. Read-only — never mutates state.

Run:

```powershell
.\core\bin\guia.ps1 status
```

Or pass a specific task id:

```powershell
.\core\bin\guia.ps1 status <D-NNN>
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py status [<D-NNN>]`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
