---
name: guia-fluxo
description: "REFERENCE/BACKGROUND ONLY — overview of the Guia Fluxo task-process pipeline (D-NNN tasks, status states, locks, chat-rename, worktree). Use directly when the developer asks for the process overview (\"explain Guia Fluxo\", \"how does this pipeline work\"), the installation guide, or the portability checklist. Not a competitor to the action verbs — those route to their own shims first."
---

# Guia Fluxo

Reference for the repository's task-process pipeline. Use this skill when the developer wants the **process overview** — what verbs exist, who triggers what, how the moving parts fit. The action playbook for each verb lives in the verb's own shim plus shared partials in `core/manifest/bodies/_partials/`.

## Trigger Commands

Legend: 👤 human triggers | 🤖 agent triggers | 👤→🤖 human authorizes, agent executes.

Slash-command prefix differs by host: Claude Code exposes the plugin namespace (`/guia:feature`), Codex/Antigravity use bare verbs (`/feature` or `$feature`). The verb semantics are identical.

- 👤 `feature <title>`: create a new `D-NNN` feature task.
- 👤 `bug <title>`: create a new `D-NNN` bug task.
- 👤 `chore <title>`: create a new `D-NNN` chore task.
- 👤 `backlog add <title>`: park future work without starting implementation.
- 👤 `backlog list`: show parked work.
- 👤 `promote <B-NNN>`: agent evaluates the backlog item, proposes a plan, asks worktree yes/no, then promotes after developer OK.
- 👤 `status [<D-NNN>]`: show active task and its demand title.
- 🤖 `ready [<D-NNN>]`: handoff to validation. **The agent itself runs this when implementation ends** — never the human, never as a shortcut to skip ahead to `finish`.
- 👤→🤖 `finish [<D-NNN>]`: close an already-validated task. The human confirms validation in real use; the agent runs the command.
- 👤 `init`: one-time setup of Guia Fluxo in this project — seed `.guia/` and deploy the lock config + `commit-msg` hook. Usually optional (the engine auto-creates `.guia/` on the first command); run it to opt into file locks.

## Core Rule

Use the engine as the source of truth.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
feature "Short title" --context "Why this matters"
bug "Bug title" --context "Observed failure"
backlog add "Future idea" --context "Useful later"
promote B-001 --kind feature --assessment "Clear feature" --plan "Inspect affected files"
status
ready D-016 --file core/src/guia.py --summary "Implemented Guia Fluxo CLI"
finish D-016 --lock --lock-id guia-fluxo
```

Do not hand-generate IDs, status blocks, backlog records, or current-task records when the engine can do it.

## Where Behavior Lives

The per-verb action playbook is in each verb's shim body, which composes shared partials:

- `_partials/title_context_rules.md` — how to synthesize `<title>` vs `<context>` (feature, bug, chore, backlog).
- `_partials/run_cmd.agent.md` / `_partials/run_cmd.claude.md` — host-aware invocation. The agent host (Codex/Antigravity) calls the repo wrapper `core/bin/guia.ps1`; the Claude host calls the plugin-bundled engine via `${CLAUDE_PLUGIN_ROOT}/bin/guia.py` (no repo clone). The include `{{include_per_target: _partials/run_cmd}}` in each verb body picks the right one at build time.
- `_partials/post_cli.agent.md` / `_partials/post_cli.claude.md` — post-CLI flow per host (read `.guia/current-task.json`, repeat `NOME DA DEMANDA`, optionally rename the chat). The host-aware include `{{include_per_target: _partials/post_cli}}` in each verb body picks the right one at build time.
- `_partials/lock_protocol.md` — `.guia/locks/registry.yaml` enforcement and unlock request flow (used by any verb that edits files).

Editing a partial changes every shim that uses it. This skill (`guia-fluxo`) is intentionally **not** part of that action chain — it stays as reference.

## Tool Notes per Host

- **Codex** does not treat arbitrary `/feature` or `/finish` as custom slash commands in every surface. Reliable Codex calls are direct script commands, `/use guia-fluxo`, or shim skills such as `$finish` after skills reload.
- **Antigravity** reads skills from the same `plugins/guia/.agents/skills/` tree as Codex. The shim skills in this pack work for both surfaces; treat any verb listed above as a callable workflow. No thread-rename API available — chat title falls back to printed text.
- **Claude Code** reads this pack as an official plugin: `plugins/guia/.claude-plugin/plugin.json` (name `guia`) exposes each verb as a plugin **command** in `plugins/guia/commands/<verb>.md`, so the shortcuts surface namespaced as `/guia:feature`, `/guia:bug`, `/guia:chore`, `/guia:backlog`, `/guia:promote`, `/guia:ready`, `/guia:finish`, `/guia:status`, `/guia:init` — plugin *skills* would surface bare (`/init`, `/feature`) and collide with built-ins like `/init`. Claude also auto-invokes a command by its `description`. All bodies are generated from `core/manifest/manifest.yaml`.

## Chat Rename per Host

The script prints `NOME DA DEMANDA: ...` — info about the current demand; the script itself does **not** rename the chat. **One demand, one chat (D-185):** a demand that comes up while working another one (an epic story, a follow-up, a bug found on the way) is created with the CLI and worked in a chat of its own; only an epic's chat outlives its first demand, and it holds the epic alone. Where the host can rename the chat, the agent names it after the demand and renames it as the stage changes.

- **Codex App:** when a single demand maps to the chat, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the title printed after `NOME DA DEMANDA:`.
- **Claude Code (desktop app):** `mcp__ccd_session_mgmt__set_session_title` with `session_id: "self"` and the exact `NOME DA DEMANDA` line — a real rename, repeated on each stage change (load it with ToolSearch `select:mcp__ccd_session_mgmt__set_session_title` when deferred). A derived demand opens its own linked session with `mcp__ccd_session__start_session`, titled the same way. Without that tool: `mark_chapter` (`mcp__ccd_session__mark_chapter`, divider + ToC entry) and `/rename <demand-title>` typed by the developer; `claude -n <title>` only works when starting a new session. Do not use Codex App `codex_app.*` tools in Claude.
- **Any host without a rename API:** the printed line is enough — keep working.

**Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back. A demand started from another demand's chat (an epic's story, a follow-up from the audit or the queue) is worked in a thread of its own, which records itself.

**Controller and executor threads (D-199, ADR-0023)** - when one thread takes the developer's requests and hands each demand to a thread of its own: the **controller** splits the request into demands through the engine, follows the queue, reconciles names and runs `finish` only on the developer's authorization; the **executor** does `start` through `ready` and `next` until `stop`/`done`, reporting back. Record the roles with `chat <D-NNN> --role executor --controller <controller thread id>` (or `--role controller` for a demand the controller works itself). Authorization (unlock, approve, autonomy, configure, queue control, `finish`) is the developer's and is forwarded quoting the developer's words; nobody grants it on their own, and nobody merges the PR.

If shell access fails, surface the exact command the developer can run by hand.

## Portable install

**Claude Code (recommended — no clone).** The pack is a published plugin; install it straight from the marketplace (requires Python 3.10+ on PATH):

```text
/plugin marketplace add Paulo-Marcos/guia-fluxo
/plugin install guia@guia-fluxo
```

The bundled engine lives at `${CLAUDE_PLUGIN_ROOT}/bin/guia.py` and roots itself at the project you are working in, auto-creating `.guia/` on the first command — no clone, no copied engine. The only files that land in your project are the `.guia/` state.

Run `/guia:init` once to opt into file locks: it seeds `.guia/` and deploys the per-project lock config (`.guia/locks/registry.yaml`, `.guia/locks/lock-ignore.txt`) plus the `commit-msg` hook, then points `git core.hooksPath` at `.githooks/`. Idempotent and never clobbers existing files; skip it (or pass `--no-locks`) if you don't want locks.

**Codex / Antigravity / engine dev (manual copy).** These hosts deploy the pack into the project tree by manual copy (the `install.ps1`/`install.sh` scripts were retired in D-082), or use the source repo for engine work. Copy:

- `core/src/*.py`
- `core/bin/guia.ps1`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/` (including `_partials/`)
- `core/build/render-skills.py`
- `core/lock/lock_api.py` + `core/lock/check-lock.py`
- `core/hooks/commit-msg`
- `plugins/guia/.claude-plugin/plugin.json`
- the generated `plugins/guia/.agents/skills/*` (agent skills) and `plugins/guia/commands/*` (Claude commands) trees

Then seed the project (optional — the engine also auto-inits on first use):

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```

To regenerate the per-agent files after editing the manifest or partials:

```powershell
python core/build/render-skills.py
```
