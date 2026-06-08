---
name: promote
description: EVALUATE-AND-CONVERT one specific backlog item. Triggered ONLY by /promote <B-NNN> or "$promote B-NNN" with an explicit backlog ID. AI reads the item, asks missing questions, proposes a plan, confronts locks/risks, asks worktree y/n, then converts the B-NNN into a D-NNN task (kind feature/bug/chore). Do NOT use for: adding or listing backlog items (use $backlog), or creating a task without going through backlog first (use $feature, $bug or $chore).
---

# Promote

Evaluate and promote a backlog item into a feature, bug, or chore task.

Process:

1. Read the requested item (`$ARGUMENTS`) from `.guia/backlog.json` / `.guia/tasks.json`.
2. Decide kind: `feature`, `bug`, or `chore`.
3. Check if the item is actionable. If information is missing, ask the developer before creating a task.
4. Present a short execution plan, impacted areas, lock risks, and tradeoffs.
5. Ask whether to use a worktree.
6. After the developer approves, run:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If the developer chose worktree, include `--worktree` — branch fica `codex/<slug>` e path `.claude/worktrees/<slug>` (override com `--branch` ou `--worktree-path`). `finish` remove o worktree no fechamento.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py promote B-001 --kind feature ...`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

## File locks

Before editing files, honor `features/registry.yaml`. If a target file is locked:

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

Then execute the approved plan.
