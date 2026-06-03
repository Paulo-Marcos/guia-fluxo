# Promote Shim

Process:

1. Read `.ai/backlog.json` and find the requested `B-NNN`.
2. Decide whether it is likely `feature` or `issue`.
3. Check if title/context are actionable. If not, ask concise missing questions before creating a task.
4. Propose a short execution plan and call out risks, locked files, and likely impacted functionality.
5. Ask whether to use a worktree.
6. After user OK, run:

```powershell
.\core\bin\ai.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If user chose worktree:

```powershell
.\core\bin\ai.ps1 promote B-001 --kind feature --worktree --assessment "..." --plan "..."
```

`--worktree` creates branch `codex/<slug>` in path `.claude/worktrees/<slug>`. Override with `--branch <name>` or `--worktree-path <path>`. `finish` removes the created worktree when the task is closed.

Then continue using `ai-process`.
