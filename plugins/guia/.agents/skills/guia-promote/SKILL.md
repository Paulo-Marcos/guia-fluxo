---
name: guia-promote
description: "EVALUATE-AND-CONVERT one parked item. Takes `<B-NNN>` or `<D-NNN>` with `status=Backlog`. The agent reads the item, asks any missing question, proposes a plan, calls out locks/risks, and asks worktree y/n — only after developer OK runs the CLI. Required: `--kind feature|bug|chore`. Options: `--assessment \"<verdict>\"`, `--plan \"<step>\"` (repeatable), `--worktree`, `--branch <name>`, `--worktree-path <path>`. To add/list parked items use `backlog`; to create a task without parking first use `feature`/`bug`/`chore`."
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

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
promote B-001 --kind feature --assessment "..." --plan "..."
```

If the developer chose a worktree, include `--worktree` — branch becomes `codex/<slug>` and path `.claude/worktrees/<slug>` (override with `--branch` or `--worktree-path`). `finish` removes the worktree at closing.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**. One demand per chat (D-185): a demand that comes up while working another (an epic story, a follow-up, a bug found on the way) is created with the CLI and worked in a new thread, not in this one.
3. **Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
7. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

**Chats with an old name (D-194).** Lines `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>` (from `next`, `status`, `queue run` or `chat --pending`) name Claude Code sessions whose title fell behind the demand's stage. This host cannot rename them: show the lines to the developer and leave them pending - a Claude Code chat applies them and records `chat <D-NNN> --applied "<title>"`.

## File locks

Before editing files, honor `.guia/locks/registry.yaml`. If a target file is locked:

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
