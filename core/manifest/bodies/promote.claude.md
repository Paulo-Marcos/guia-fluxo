# Promote

Evaluate and promote a backlog item into a feature or issue.

Process:

1. Read `.ai/backlog.json` and find `$ARGUMENTS`.
2. Decide whether the item is issue or feature.
3. Check if it is actionable. If information is missing, ask the developer before creating a task.
4. Present a short execution plan, impacted areas, lock risks, and tradeoffs.
5. Ask whether to use a worktree.
6. After the developer approves, run:

```powershell
.\core\bin\ai.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If the developer chose worktree, include `--worktree` — branch fica `codex/<slug>` e path `.claude/worktrees/<slug>` (override com `--branch` ou `--worktree-path`).

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
