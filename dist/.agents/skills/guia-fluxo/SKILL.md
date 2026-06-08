---
name: guia-fluxo
description: REFERENCE/BACKGROUND ONLY for the Guia Fluxo task-process pipeline (D-NNN/B-NNN, locks, chat-rename, worktree). Loaded as context by the dedicated shims, not as a trigger competitor. Do NOT auto-fire on /feature, /bug, /chore, /backlog, /promote, /ready, /finish, /status — those route to their own shims first. Use guia-fluxo directly ONLY when the user asks for the full process overview ("explain Guia Fluxo", "how does this pipeline work", "como funciona o guia-fluxo") or needs the installation/portability guide.
---

# Guia Fluxo

Use this skill to run the repository process through deterministic scripts instead of hand-editing process files.

## Trigger Commands

Legend: 👤 human triggers | 🤖 agent triggers | 👤→🤖 human authorizes, agent executes.

- 👤 `/feature <title>`: create a new `D-NNN` feature task.
- 👤 `/bug <title>`: create a new `D-NNN` bug task.
- 👤 `/chore <title>`: create a new `D-NNN` chore task.
- 👤 `/backlog add <title>`: save future work without starting implementation.
- 👤 `/backlog list`: show future work.
- 👤 `/backlog promote <B-NNN>`: convert backlog item into a task.
- 👤 `/promote <B-NNN>`: AI evaluates backlog item, asks for missing information, proposes plan, asks worktree yes/no, then promotes it.
- 👤 `/status [D-NNN]`: show active task and suggested chat title.
- 🤖 `/ready [D-NNN]`: mark implementation as waiting for developer validation. The agent always triggers this — never the human.
- 👤→🤖 `/finish [D-NNN]`: close an already validated task, suggest `#FINALIZADO`, and commit by default. The human confirms validation; the agent runs the command.

## Core Rule

Run `core/bin/guia.ps1` or `python core/src/guia.py`. Do not manually create IDs, status blocks, backlog records, or current-task records when the script can do it.

Preferred Windows commands:

```powershell
.\core\bin\guia.ps1 feature "Short title" --context "Why this matters"
.\core\bin\guia.ps1 bug "Bug title" --context "Observed failure"
.\core\bin\guia.ps1 backlog add "Future idea" --context "Useful later"
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "Clear feature" --plan "Inspect affected files"
.\core\bin\guia.ps1 status
.\core\bin\guia.ps1 ready D-016 --file core/src/guia.py --summary "Implemented Guia Fluxo CLI"
.\core\bin\guia.ps1 finish D-016 --lock --lock-id guia-fluxo
```

Portable fallback:

```bash
python core/src/guia.py feature "Short title" --context "Why this matters"
```

## Agent Behavior

1. On `/feature`, `/bug` or `/chore`, create the task before code edits.
2. Read `.guia/current-task.json` before continuing implementation.
3. After every phase command, repeat the exact line printed by the script:
   - `NOME DO CHAT: D-016 - #DEV - Example title`
   - `NOME DO CHAT: D-016 - #VALIDACAO - Example title`
   - `NOME DO CHAT: D-016 - #FINALIZADO - Example title`
4. Rename the real chat/session, not only the visible message, whenever the host exposes a supported thread/session API.
5. In Codex App, search for the thread tools if needed, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with exactly the title printed after `NOME DO CHAT:`.
6. If no thread API is available, use that title as best-effort chat title:
   - `D-016 - #DEV - Example title`
   - `D-016 - #VALIDACAO - Example title`
   - `D-016 - #FINALIZADO - Example title`
7. Before editing files, honor `features/registry.yaml` locks.
8. If a needed file is locked, explain the lock id, protected functionality, why the edit is needed, expected impact, regression risk, and alternatives before asking for unlock.
9. On `/promote <B-NNN>`, read the backlog item first. Decide kind (feature/bug/chore), check if the request is actionable, ask missing questions if needed, propose a short execution plan, confront risks/locks, and ask whether to use worktree. Only after user OK, run `.\core\bin\guia.ps1 promote ...`.
10. If user chooses worktree, pass `--worktree`; the task stores worktree metadata and `finish` removes it when closing.
11. The agent MUST call `/ready` itself when implementation ends — never wait for the human to ask, and never skip ahead to `/finish`. On `/ready`, register changed files, summary, validations, and pending manual validation.
12. On `/finish`, only close when the developer says the work is validated/final. Commit is on by default; pass `--no-commit` for dry close.
13. Use `--lock` on `/finish` only when the developer asks to create/update the lock.

## Tool Notes

- Codex does not treat arbitrary `/feature` or `/finish` as custom slash commands in every surface. Reliable Codex calls are direct script commands, `/use guia-fluxo`, or shim skills such as `$finish` after skills reload.
- Antigravity reads skills from the same `dist/.agents/skills/` tree as Codex. The shim skills in this pack work for both surfaces; treat any verb listed above as a callable workflow.
- Claude Code reads this pack as an official plugin: `dist/.claude-plugin/plugin.json` (name `guia`) exposes the skills in `dist/skills/<verb>/SKILL.md` under namespace `guia`. Atalhos no Claude saem `/guia:feature`, `/guia:bug`, `/guia:chore`, `/guia:backlog`, `/guia:promote`, `/guia:ready`, `/guia:finish`, `/guia:status`. Claude also loads skills automatically by description. All bodies are generated from `core/manifest/manifest.yaml`.
- Codex App chat rename is explicit: printing `NOME DO CHAT: ...` does not rename the UI. Use `codex_app.list_threads` to find the current thread id and `codex_app.set_thread_title` with the exact suggested title. If those tools are not loaded, search for thread tools first.
- Claude chat rename: use `/rename <suggested-title>` when Claude Code exposes it, or start a session with `claude -n <suggested-title>` when that flag is supported. Claude does not use Codex App `codex_app.*` tools.
- If a host cannot rename from the agent turn, print the suggested title and keep working.
- If shell access fails, explain the exact command the developer can run.

## Portability

This skill is intentionally project-neutral. To reuse it elsewhere, copy:

- `.guia/process.json`
- `core/src/guia.py`
- `core/bin/guia.ps1`
- `core/manifest/manifest.yaml`
- `core/build/render-skills.py`
- `core/lock/check-lock.py`
- `core/hooks/commit-msg`
- `dist/.claude-plugin/plugin.json` (plugin manifest) + `dist/.claude-plugin/marketplace.json`
- the generated `dist/.agents/skills/*` and `dist/skills/*` trees

Then run:

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```

To regenerate the per-agent files after editing the manifest:

```powershell
python core/build/render-skills.py
```
