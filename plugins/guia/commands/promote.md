---
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
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**; in this demand's own chat it is also the chat title (step 4).
3. **One demand, one chat, on the recommended model (D-185).** A chat belongs to one demand. Run the triage of step 5 **first**, then decide where the demand runs:
   - **Work it here** only when this chat holds no other demand **and** runs on the recommended model.
   - **Otherwise open its own chat** - a demand that comes up while working another (an epic story, a follow-up, a bug found on the way), or a recommended model different from this chat's. Create it with the CLI (`--status planned`, or `--under E-NNN` for a story), then call `start_session` (`mcp__ccd_session__start_session`; load it with ToolSearch `select:mcp__ccd_session__start_session` when deferred) with: `title` = its `NOME DA DEMANDA` line in the Guia format `D-NNN <emoji> - #<STAGE> - <title>` (e.g. `D-186 🐛 - #PLANEJADA - ...`; the new chat renames itself to `#DEV` when it runs `start`); `model` = the model id of the recommended family and `effort` = the recommended effort (`triage <D-NNN> --json` gives both); `context: "fresh"`; a brief that starts with `start <D-NNN>`. `initiation`: `"offer"` when the developer named the demand in their message, `"user_asked"` when they told you to start it, `"own_initiative"` when you found it. The app links the new session to this one.
   - `start_session` only lowers the model. When the recommendation is above this chat's (e.g. Opus from a Sonnet chat, or a Fable suggestion), say so and let the developer switch - never assume it.
   - An epic's chat holds the epic alone: each story runs in its own linked chat.
4. **Name the chat after the demand, and keep it current (D-185)** - every time the script prints `NOME DA DEMANDA` in this demand's chat (create, start, ready, ship, queue add, block...):
   - Rename the session to that exact line - the Guia format `D-NNN <emoji> - #<STAGE>[·<level>] - <title>`, never a free-form name - with `mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`). When the tool is deferred, load it first with ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. The title then follows the stage (`#DEV` -> `#VALIDACAO` -> `#PR`...), so the sidebar shows where each demand is.
   - Without that tool (CLI, another host, an unattended session that declines it): fall back to `mark_chapter` (`mcp__ccd_session__mark_chapter`, divider + ToC entry) and tell the developer the name to `/rename`.
   - **Record it once (D-157):** run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`, ID + title, no stage) and save it with `chat <D-NNN> --title "<name>"`. The queue, `next` and `status --all` cite it ("volte ao chat: ..."); the live title starts with the same `D-NNN`, so searching the sidebar for the ID finds it. **Always show the chat name to the developer**, even when renaming is not available.
5. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat, before step 3 decides where it runs: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, step 3 opens the demand's chat on the recommended one (lower) or tells the developer (higher). A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
6. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

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
