---
name: guia-promote
description: EVALUATE-AND-CONVERT one specific backlog item. Triggered ONLY by /promote <B-NNN> or "$promote B-NNN" with an explicit backlog ID. AI reads the item, asks missing questions, proposes a plan, confronts locks/risks, asks worktree y/n, then converts the B-NNN into a D-NNN task (kind feature/bug/chore). Do NOT use for: adding or listing backlog items (use $backlog), or creating a task without going through backlog first (use $feature, $bug or $chore).
---

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

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

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

Then execute the approved plan, following `guia-fluxo` for cross-cutting protocol.
