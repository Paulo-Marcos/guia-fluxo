Evaluate and promote a backlog item into a feature or issue.

Process:

1. Read `.ai/backlog.json` and find `$ARGUMENTS`.
2. Decide whether the item is issue or feature.
3. Check if it is actionable. If information is missing, ask Paulo before creating a task.
4. Present a short execution plan, impacted areas, lock risks, and tradeoffs.
5. Ask whether to use a worktree.
6. After Paulo approves, run:

```powershell
.\scripts\ai.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If Paulo chose worktree, include `--worktree`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
