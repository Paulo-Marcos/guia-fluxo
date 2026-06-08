# Guia Fluxo

Reference for the repository's task-process pipeline. Use this skill when the developer wants the **process overview** — what verbs exist, who triggers what, how hosts differ. The action playbook for each verb lives in the verb's own shim (`feature`, `bug`, `chore`, `backlog`, `promote`, `ready`, `finish`, `status`) plus shared partials.

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

## Where Behavior Lives

The per-verb action playbook is in each verb's shim body, which composes shared partials in `core/manifest/bodies/_partials/`:

- `title_context_rules.md` — how to synthesize `<title>` vs `<context>` (used by feature, bug, chore, backlog).
- `post_cli.agent.md` / `post_cli.claude.md` — post-CLI flow: read `current-task.json`, repeat `NOME DO CHAT`, rename chat (host-specific).
- `lock_protocol.md` — `features/registry.yaml` enforcement, unlock request flow (used by any verb that edits files).

Editing a partial changes every shim that uses it. This skill (`guia-fluxo`) is intentionally **not** part of that action chain — it stays as reference.

## Tool Notes

- Codex does not treat arbitrary `/feature` or `/finish` as custom slash commands in every surface. Reliable Codex calls are direct script commands, `/use guia-fluxo`, or shim skills such as `$finish` after skills reload.
- Antigravity reads skills from the same `dist/.agents/skills/` tree as Codex. The shim skills in this pack work for both surfaces; treat any verb listed above as a callable workflow.
- Claude Code reads this pack as an official plugin: `dist/.claude-plugin/plugin.json` (name `guia`) exposes the skills in `dist/skills/<verb>/SKILL.md` under namespace `guia`. Atalhos no Claude saem `/guia:feature`, `/guia:bug`, `/guia:chore`, `/guia:backlog`, `/guia:promote`, `/guia:ready`, `/guia:finish`, `/guia:status`. Claude also loads skills automatically by description. All bodies are generated from `core/manifest/manifest.yaml`.
- Codex App chat rename: print `NOME DO CHAT: ...` AND call `codex_app.list_threads` + `codex_app.set_thread_title` with the exact suggested title. The print alone does not rename the UI.
- Claude Code chat rename: call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the suggested title — reliable surrogate that places a divider + ToC entry. Also try `/rename <suggested-title>` if the slash command is exposed. `claude -n <title>` works only when starting a new session.
- If a host cannot rename from the agent turn, print the suggested title and keep working.
- If shell access fails, explain the exact command the developer can run.

## Portability

This skill is intentionally project-neutral. To reuse it elsewhere, copy:

- `.guia/process.json`
- `core/src/guia.py`
- `core/bin/guia.ps1`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/` (including `_partials/`)
- `core/build/render-skills.py`
- `core/lock/check-lock.py`
- `core/hooks/commit-msg`
- `dist/.claude-plugin/plugin.json` (plugin manifest) + `dist/.claude-plugin/marketplace.json`
- the generated `dist/.agents/skills/*` and `dist/skills/*` trees

Then run:

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```

To regenerate the per-agent files after editing the manifest or partials:

```powershell
python core/build/render-skills.py
```
