---
description: EVALUATE-AND-CONVERT one parked item. Takes `<B-NNN>` or `<D-NNN>` with `status=Backlog`. The agent reads the item, asks any missing question, proposes a plan, calls out locks/risks, and asks worktree y/n — only after developer OK runs the CLI. Required: `--kind feature|bug|chore`. Options: `--assessment "<verdict>"`, `--plan "<step>"` (repeatable), `--worktree`, `--branch <name>`, `--worktree-path <path>`. To add/list parked items use `backlog`; to create a task without parking first use `feature`/`bug`/`chore`.
---

# Promote

Evaluate one backlog item and convert it into an in-development task. The agent does the evaluation; the developer authorizes.

Process:

1. Read the requested item (`<B-NNN>` or `<D-NNN>` with status=Backlog) from `.guia/backlog.json` / `.guia/tasks.json`.
2. Decide kind: `feature`, `bug`, or `chore`.
3. Check if title/context are actionable. If information is missing, ask the developer before creating a task.
4. Propose a short execution plan, impacted areas, lock risks, and tradeoffs.
5. Ask whether to use a worktree.
6. After the developer approves, run the command below.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
promote B-001 --kind feature --assessment "..." --plan "..."
```

If the developer chose a worktree, include `--worktree` — branch becomes `codex/<slug>` and path `.claude/worktrees/<slug>` (override with `--branch` or `--worktree-path`). `finish` removes the worktree at closing.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

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

Then execute the approved plan.
