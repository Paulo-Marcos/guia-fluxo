---
description: "EPIC — create an `E-NNN` epic to orchestrate a large piece of work that breaks down into smaller stories (D-049). The epic itself does no implementation; it aggregates children. Use `feature/bug/chore \"...\" --under E-NNN` to attach a child story; `status E-NNN` prints the aggregated tree (closed/total children); `finish E-NNN` is REFUSED while any child is in a non-terminal status (Em desenvolvimento / Aguardando validacao / Planejada / Backlog / Bloqueada). No nested epics (2-level hierarchy only). `cancel` on an epic does NOT cascade: children remain as-is."
---

# Epic

Create an **Epic** (`E-NNN`) — an orchestrator for a large piece of work that breaks down into smaller **stories** (`D-NNN`). The epic itself does no implementation: it aggregates children and gates closure. This is the answer to "this demand is too big to fit in one chat" without losing rastreio.

The `title` is a short imperative phrase naming the whole effort ("Migrar X para Y", "Reformular fluxo de Z"). Use `--context "..."` to justify why this needed to be an epic and not a single demand.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
epic "Reformular fluxo X" --context "Por que isso virou epic"
feature "Tela Y" --under E-001            # cria D-NNN como filho de E-001
bug "Bug Z" --under E-001                 # tambem aceita
chore "Limpar legado W" --under E-001     # tambem
status E-001                              # arvore agregada (filhos + status)
finish E-001                              # SO fecha quando todos os filhos forem terminais
```

## Rules and guarantees

- **Own numbering.** Epics are `E-NNN`; stories are `D-NNN`. They never collide visually.
- **2-level hierarchy.** No nested epics. `--under` only accepts an Epic id; otherwise the command is refused.
- **`status E-NNN`** prints the tree with `Progresso: closed/total` and lists every child with its current status. If any child is open, prints the blockage notice.
- **`finish E-NNN`** is **refused** while any child is in a non-terminal status (`Em desenvolvimento`, `Aguardando validacao`, `Planejada`, `Backlog`, `Bloqueada`). Terminal statuses that count as "done for the epic": `Validada`, `Finalizada`, `Resolvida`, `Cancelada`.
- **`cancel E-NNN`** does **not** cascade to children. Cancelling the epic just terminates the parent; each child stays as-is and you decide caso a caso.
- **`parentId` is immutable.** To move a story between epics, cancel it and recreate under the new parent.

## When to use

- A demand that won't fit in one chat / one PR.
- A migration with several visible deliverables.
- A coordinated cross-area change (frontend + backend + docs) where each side has its own story.

## When NOT to use

- A single demand that just needs `--depends-on` to wait for another (use D-067, not D-049).
- A two-line refactor that doesn't deserve a chat-pai. Just use `chore`.

Reflect the printed `NOME DA DEMANDA` for the epic itself (`E-NNN ✨ - #DEV - <title>`) and name this chat after it (below). The epic's chat holds the epic alone (D-185): each story is created here with `--under E-NNN --status planned` and then runs in **its own linked chat** (`start_session`, titled with the story's `NOME DA DEMANDA`, brief starting with `start <D-NNN>`). Never `start` the stories in batch here: a story started in the epic's chat records no chat of its own, and the queue cannot rename it when it integrates (D-190). Come back to the epic's chat for `epic status` and the epic's `finish`.

**Name this chat after the demand and record its session (D-185, D-188, D-190)** - in the chat that works the demand, every time the script prints `NOME DA DEMANDA` (create, start, unblock, ready, ship, queue add, block...):

- **Rename** the session to that exact line - the Guia format `D-NNN <emoji> - #<STAGE>[·<level>] - <title>`, never a free-form name - with `mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`). When the tool is deferred, load it first with ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. The title then follows the stage (`#DEV` -> `#VALIDACAO` -> `#PR`...), so the sidebar shows where each demand is.
- **Record it once:** `chat <D-NNN>` prints the stable name (`NOME DO CHAT: ...`, ID + title, no stage). Get this chat's `sessionId` from `mcp__ccd_session_mgmt__get_session` (`session_id: "self"`; load it with ToolSearch `select:mcp__ccd_session_mgmt__get_session` when deferred) and save both with `chat <D-NNN> --title "<name>" --session <sessionId>`. Always the real id (`local_...`), never the literal `self`. With the session recorded, any Guia chat renames this chat when its stage moves on - up to `#INTEGRADA`/`#FINALIZADO` when the queue integrates the demand (D-188, D-194); without it nobody can. Until it is recorded, `next` and `status` print `AVISO CHAT: ...` with the command.
- **One chat per demand, never a batch.** A demand started from another demand's chat - an epic's story, a follow-up opened by the audit or by the queue - does not belong to this chat: open its own with `start_session` (titled with its `NOME DA DEMANDA`, brief starting with `start <D-NNN>`), and that chat renames and records itself.
- **Without the tool** (CLI, another host, an unattended session that declines it): fall back to `mark_chapter` (`mcp__ccd_session__mark_chapter`, divider + ToC entry), tell the developer the name to `/rename`, and record with `chat <D-NNN> --title "<name>"` (no `--session`). **Always show the chat name to the developer**, even when renaming is not available - the queue, `next` and `status --all` cite it ("volte ao chat: ...").

**Controller and executor chats (D-199, ADR-0023)** - when one chat takes the developer's requests and opens one session per demand:

- **Controller** (the main chat): diagnoses and splits the request into demands through the engine (`feature`/`bug`/`chore` + `triage`); opens one executor per demand with `start_session` (`model`/`effort` from `triage --json`, brief starting with `start <D-NNN>`, the Guia worktree); follows the queue and unblocks it (a conflict -> tell the executor to rebase, re-audit and `queue add`); reconciles the chats' names (`chat --pending`); runs `finish` (docs-check + quality review) only on the developer's authorization; opens the release. A demand it works itself (the epic, the release) is recorded with `chat <D-NNN> --role controller`.
- **Executor** (one session per demand): `start` through `ready`, then `next` until `stop`/`done`, in the demand's worktree; reports back to the controller, and asks it ONE short question when blocked on a decision that is the developer's.
- **Who opens the session records it.** Right after `start_session` returns, whoever called it - the controller, or a developer-driven chat with no controller - records the new session on that demand: `chat <D-NNN> --title "<name>" --session <new sessionId> --role executor --controller <controller sessionId>`. A follow-up inherits the controller of the demand it came from (`chat <origin> --json`). On `start`, the executor confirms its own record: its `sessionId` from `get_session("self")`, and the controller already recorded on the demand or named in the brief; only without either, that call's `parentSessionId` (for a follow-up an executor proposed, the parent is that executor, not the controller). Without the session, the follow-up never enters `chat --pending` and its chat is renamed by hand; `chat --pending` lists such demands as `AVISO CHAT: ...`.
- **The controller coordinates; the executor proposes (D-210, ADR-0025).** The developer decides everything from the controller, and the tendency is to open sessions too many:
  - **Follow-up = proposal.** An executor that finds new work (a bug on the way, a follow-up) never calls `start_session`: it creates the demand with `--status planned --from <its D-NNN>` (the engine copies the controller onto it and prints `PROPOSTA: ...`) and tells the controller in its report. Only the controller opens sessions.
  - **One board:** the controller runs `guia controle` (`--session <its sessionId>`, `--json`) instead of piecing the state together from notes: each executor with its stage, PR and who holds the ball (`dono`, `fila` or `executora`, from the same `next` that conducts the demand), the open questions, the proposals waiting for a session, the sessions to archive and the free slots.
  - **Questions in a queue, not one message each:** the executor records `ask <D-NNN> "<question>" --option "<A>" --option "<B>"` and sends the controller one short line; the controller shows every open `PERGUNTA` together to the developer, records the answer in the developer's words with `answer <D-NNN> P<n> --quote "<words>"`, and takes the printed `LEVE A EXECUTORA: ...` line, quoted, to that executor.
  - **Archive what is done, with the developer's ok:** for each `ARQUIVE COM OK DO DONO: <sessionId> ...` the controller asks the developer once (all together); on a yes, `mcp__ccd_session_mgmt__archive_session` (reversible: `unarchive_session`) and `chat <D-NNN> --archived` (`--unarchived` undoes).
  - **Slot limit:** at most `controller.maxExecutors` open executors (`.guia/process.json`, default 4). With no free slot (`SEM VAGA`, `ACIMA DO LIMITE`), the controller does not open a session: the demand waits `Planejada` and it tells the developer.
- **Authorization is the developer's, in the developer's words.** Neither role grants anything on its own: unlock, approve, autonomy, configure, `queue run`/`pause`/`resume` and `finish` stay the developer's (D-098, `queue-control`). The controller forwards an authorization quoting what the developer said; the executor acts only on an authorization quoted that way. Neither merges the PR.
