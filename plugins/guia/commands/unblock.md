---
description: "RESUME a paused task — moves status from `Bloqueada` back to `Em desenvolvimento`. Inverse of `block`. Options: `--note \"<what unblocked>\"`. Fails if the task wasn't `Bloqueada` (preserves flow states)."
---

# Unblock

**Resume a paused task.** Moves status from `Bloqueada` back to `Em desenvolvimento`. Use after `block` once the dependency/decision blocking the work has been resolved.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
unblock <D-NNN> [--note "What unblocked it"]
```

`--note` is optional — useful when it is worth recording what unblocked it (decision made, dependency resolved).

Fails if the task was not in `Bloqueada` (preserves the flow states).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**; in this demand's own chat it is also the chat title (step 4).
3. **One demand, one chat, on the recommended model (D-185).** A chat belongs to one demand. Run the triage of step 5 **first**, then decide where the demand runs:
   - **Work it here** only when this chat holds no other demand **and** runs on the recommended model.
   - **Otherwise open its own chat** - a demand that comes up while working another (an epic story, a follow-up, a bug found on the way), or a recommended model different from this chat's. Create it with the CLI (`--status planned`, or `--under E-NNN` for a story), then call `start_session` (`mcp__ccd_session__start_session`; load it with ToolSearch `select:mcp__ccd_session__start_session` when deferred) with: `title` = its `NOME DA DEMANDA` line in the Guia format `D-NNN <emoji> - #<STAGE> - <title>` (e.g. `D-186 🐛 - #PLANEJADA - ...`; the new chat renames itself to `#DEV` when it runs `start`); `model` = the model id of the recommended family and `effort` = the recommended effort (`triage <D-NNN> --json` gives both); `context: "fresh"`; a brief that starts with `start <D-NNN>`. `initiation`: `"offer"` when the developer named the demand in their message, `"user_asked"` when they told you to start it, `"own_initiative"` when you found it. The app links the new session to this one. Once the session exists (the tool result gives its id), record it on the demand - `chat <D-NNN> --title "<name>" --session <new sessionId> --role executor --controller <controller sessionId>` (D-199: who opens the session records it, follow-ups included).
   - `start_session` only lowers the model. When the recommendation is above this chat's (e.g. Opus from a Sonnet chat, or a Fable suggestion), say so and let the developer switch - never assume it.
   - An epic's chat holds the epic alone: each story runs in its own linked chat.
4. **Name the chat after the demand and record its session** - the block below this list (D-185, D-188, D-190).
5. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat, before step 3 decides where it runs: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, step 3 opens the demand's chat on the recommended one (lower) or tells the developer (higher). A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
6. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

**Reconcile the chats' names (D-194)** - whenever the script prints lines `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>` (`next`, `status`, `queue run`, or `chat --pending` on demand), some demand's chat - this one or another - still carries an old stage. For each line:

- call `mcp__ccd_session_mgmt__set_session_title` with `session_id: "<sessionId>"` and `title` = the text after `-> `, exactly as printed (load it with ToolSearch `select:mcp__ccd_session_mgmt__set_session_title` when deferred);
- then record what happened: `chat <D-NNN> --applied "<title>"` when it renamed, or `chat <D-NNN> --refused "<title>" --reason "<why>"` when the app declined (the owner's own title, an archived or unattended session). A refusal is a warning, shown once: the engine does not ask again until the demand's stage changes, so never retry it in a loop.

Nobody needs to be the queue manager: any Guia chat that sees the lines applies them, and the engine stops listing a session once its name matches. The session is always the real id (`local_...` from `get_session`), never the literal `self` - `chat --session self` is refused.

**Name this chat after the demand and record its session (D-185, D-188, D-190)** - in the chat that works the demand, every time the script prints `NOME DA DEMANDA` (create, start, unblock, ready, ship, queue add, block...):

- **Rename** the session to that exact line - the Guia format `D-NNN <emoji> - #<STAGE>[·<level>] - <title>`, never a free-form name - with `mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`). When the tool is deferred, load it first with ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. The title then follows the stage (`#DEV` -> `#VALIDACAO` -> `#PR`...), so the sidebar shows where each demand is.
- **Record it once:** `chat <D-NNN>` prints the stable name (`NOME DO CHAT: ...`, ID + title, no stage). Get this chat's `sessionId` from `mcp__ccd_session_mgmt__get_session` (`session_id: "self"`; load it with ToolSearch `select:mcp__ccd_session_mgmt__get_session` when deferred) and save both with `chat <D-NNN> --title "<name>" --session <sessionId>`. Always the real id (`local_...`), never the literal `self`. With the session recorded, any Guia chat renames this chat when its stage moves on - up to `#INTEGRADA`/`#FINALIZADO` when the queue integrates the demand (D-188, D-194); without it nobody can. Until it is recorded, `next` and `status` print `AVISO CHAT: ...` with the command.
- **One chat per demand, never a batch.** A demand started from another demand's chat - an epic's story, a follow-up opened by the audit or by the queue - does not belong to this chat: open its own with `start_session` (titled with its `NOME DA DEMANDA`, brief starting with `start <D-NNN>`), and that chat renames and records itself.
- **Without the tool** (CLI, another host, an unattended session that declines it): fall back to `mark_chapter` (`mcp__ccd_session__mark_chapter`, divider + ToC entry), tell the developer the name to `/rename`, and record with `chat <D-NNN> --title "<name>"` (no `--session`). **Always show the chat name to the developer**, even when renaming is not available - the queue, `next` and `status --all` cite it ("volte ao chat: ...").

**Controller and executor chats (D-199, ADR-0023)** - when one chat takes the developer's requests and opens one session per demand:

- **Controller** (the main chat): diagnoses and splits the request into demands through the engine (`feature`/`bug`/`chore` + `triage`); opens one executor per demand with `start_session` (`model`/`effort` from `triage --json`, brief starting with `start <D-NNN>`, the Guia worktree); follows the queue and unblocks it (a conflict -> tell the executor to rebase, re-audit and `queue add`); reconciles the chats' names (`chat --pending`); runs `finish` (docs-check + quality review) only on the developer's authorization; opens the release. A demand it works itself (the epic, the release) is recorded with `chat <D-NNN> --role controller`.
- **Executor** (one session per demand): `start` through `ready`, then `next` until `stop`/`done`, in the demand's worktree; reports back to the controller, and asks it ONE short question when blocked on a decision that is the developer's.
- **Who opens the session records it.** Right after `start_session` returns, whoever called it - the controller, or an executor opening a follow-up - records the new session on that demand: `chat <D-NNN> --title "<name>" --session <new sessionId> --role executor --controller <controller sessionId>`. A follow-up inherits the controller of the demand it came from (`chat <origin> --json`). On `start`, the executor confirms its own record: its `sessionId` from `get_session("self")`, and the controller from that call's `parentSessionId` (or from the brief). Without the session, the follow-up never enters `chat --pending` and its chat is renamed by hand; `chat --pending` lists such demands as `AVISO CHAT: ...`.
- **Authorization is the developer's, in the developer's words.** Neither role grants anything on its own: unlock, approve, autonomy, configure, `queue run`/`pause`/`resume` and `finish` stay the developer's (D-098, `queue-control`). The controller forwards an authorization quoting what the developer said; the executor acts only on an authorization quoted that way. Neither merges the PR.
