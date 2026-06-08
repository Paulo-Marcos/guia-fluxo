# Promote Shim

Evaluate one backlog item and convert it into an in-development task. The agent does the evaluation; the developer authorizes.

Process:

1. Read the requested `B-NNN` (or `D-NNN` with status=Backlog) from `.guia/backlog.json` / `.guia/tasks.json`.
2. Decide whether it is `feature`, `bug`, or `chore`.
3. Check if title/context are actionable. If not, ask concise missing questions before creating a task.
4. Propose a short execution plan and call out risks, locked files, and likely impacted functionality.
5. Ask whether to use a worktree.
6. After developer OK, run:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If developer chose worktree:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --worktree --assessment "..." --plan "..."
```

`--worktree` creates branch `codex/<slug>` in path `.claude/worktrees/<slug>`. Override with `--branch <name>` or `--worktree-path <path>`. `finish` removes the created worktree when the task is closed.

{{include: _partials/post_cli.agent.md}}

{{include: _partials/lock_protocol.md}}

Then execute the approved plan, following `guia-fluxo` for cross-cutting protocol.
