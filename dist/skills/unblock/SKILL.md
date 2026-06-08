---
name: unblock
description: RESUME a paused task — move status de `Bloqueada` para `Em desenvolvimento`. Triggered by /unblock or "$unblock" / "retomar tarefa / desbloquear / dependencia resolvida". Inverso de $block. Falha se a task nao estava em `Bloqueada`. Do NOT use for: criar nova task (use $feature, $bug ou $chore), promover backlog (use $promote), ou voltar de cancelamento (cancelamento e terminal - abra nova task).
---

# Unblock

**Resume a paused task.** Moves status from `Bloqueada` back to `Em desenvolvimento`. Use after `block` once the dependency/decision blocking the work has been resolved.

Run:

```powershell
.\core\bin\guia.ps1 unblock <D-NNN> [--note "What unblocked it"]
```

`--note` is optional — useful when it is worth recording what unblocked it (decision made, dependency resolved).

Fails if the task was not in `Bloqueada` (preserves the flow states).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py unblock <D-NNN>`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
