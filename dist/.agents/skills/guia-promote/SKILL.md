---
name: guia-promote
description: EVALUATE-AND-CONVERT one specific backlog item. Triggered ONLY by /promote <B-NNN> or "$promote B-NNN" with an explicit backlog ID. AI reads the item, asks missing questions, proposes a plan, confronts locks/risks, asks worktree y/n, then converts the B-NNN into a D-NNN task (kind feature/bug/chore). Do NOT use for: adding or listing backlog items (use $backlog), or creating a task without going through backlog first (use $feature, $bug or $chore).
---

# Promote Shim

Process:

1. Read `.guia/backlog.json` and find the requested `B-NNN`.
2. Decide whether it is likely `feature` or `issue`.
3. Check if title/context are actionable. If not, ask concise missing questions before creating a task.
4. Propose a short execution plan and call out risks, locked files, and likely impacted functionality.
5. Ask whether to use a worktree.
6. After user OK, run:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "..." --plan "..."
```

If user chose worktree:

```powershell
.\core\bin\guia.ps1 promote B-001 --kind feature --worktree --assessment "..." --plan "..."
```

`--worktree` creates branch `codex/<slug>` in path `.claude/worktrees/<slug>`. Override with `--branch <name>` or `--worktree-path <path>`. `finish` removes the created worktree when the task is closed.

Then continue using `guia-fluxo`.
