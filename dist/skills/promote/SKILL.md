---
name: promote
description: EVALUATE-AND-CONVERT one specific backlog item. Triggered ONLY by /promote <B-NNN> or "$promote B-NNN" with an explicit backlog ID. AI reads the item, asks missing questions, proposes a plan, confronts locks/risks, asks worktree y/n, then converts the B-NNN into F-NNN or I-NNN. Do NOT use for: adding or listing backlog items (use $backlog), or creating a task without going through backlog first (use $feature or $issue).
---

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

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py promote B-001 --kind feature ...`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
