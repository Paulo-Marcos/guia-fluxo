---
name: promote
description: EVALUATE-AND-CONVERT one specific backlog item. Triggered ONLY by /promote <B-NNN> or "$promote B-NNN" with an explicit backlog ID. AI reads the item, asks missing questions, proposes a plan, confronts locks/risks, asks worktree y/n, then converts the B-NNN into F-NNN or I-NNN. Do NOT use for: adding or listing backlog items (use $backlog), or creating a task without going through backlog first (use $feature or $issue).
---

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

`finish` removes the created worktree when the task is closed.
