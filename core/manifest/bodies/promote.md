# Promote

Evaluate one backlog item and convert it into an in-development task. The agent does the evaluation; the developer authorizes.

Process:

1. Read the requested item (`<B-NNN>` or `<D-NNN>` with status=Backlog) from `.guia/backlog.json` / `.guia/tasks.json`.
2. Decide kind: `feature`, `bug`, or `chore`.
3. Check if title/context are actionable. If information is missing, ask the developer before creating a task.
4. Propose a short execution plan, impacted areas, lock risks, and tradeoffs.
5. Ask whether to use a worktree.
6. After the developer approves, run:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If the developer chose a worktree, include `--worktree` — branch becomes `codex/<slug>` and path `.claude/worktrees/<slug>` (override with `--branch` or `--worktree-path`). `finish` removes the worktree at closing.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py promote B-001 --kind feature ...`.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then execute the approved plan.
