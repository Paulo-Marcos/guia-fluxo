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

{{include: _partials/post_cli.claude.md}}

{{include: _partials/lock_protocol.md}}

Then execute the approved plan.
