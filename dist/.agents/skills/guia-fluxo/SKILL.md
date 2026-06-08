---
name: guia-fluxo
description: REFERENCE/BACKGROUND ONLY for the Guia Fluxo task-process pipeline (D-NNN/B-NNN, locks, chat-rename, worktree). Loaded as context by the dedicated shims, not as a trigger competitor. Do NOT auto-fire on /feature, /bug, /chore, /backlog, /promote, /ready, /finish, /status — those route to their own shims first. Use guia-fluxo directly ONLY when the user asks for the full process overview ("explain Guia Fluxo", "how does this pipeline work", "como funciona o guia-fluxo") or needs the installation/portability guide.
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
- 👤 `status [<D-NNN>]`: show active task and suggested chat title.
- 🤖 `ready [<D-NNN>]`: handoff to validation. **The agent itself runs this when implementation ends** — never the human, never as a shortcut to skip ahead to `finish`.
- 👤→🤖 `finish [<D-NNN>]`: close an already-validated task. The human confirms validation in real use; the agent runs the command.

## Core Rule

Use repository scripts as the source of truth:

```powershell
.\core\bin\guia.ps1 feature "Short title" --context "Why this matters"
.\core\bin\guia.ps1 bug "Bug title" --context "Observed failure"
.\core\bin\guia.ps1 backlog add "Future idea" --context "Useful later"
.\core\bin\guia.ps1 promote B-001 --kind feature --assessment "Clear feature" --plan "Inspect affected files"
.\core\bin\guia.ps1 status
.\core\bin\guia.ps1 ready D-016 --file core/src/guia.py --summary "Implemented Guia Fluxo CLI"
.\core\bin\guia.ps1 finish D-016 --lock --lock-id guia-fluxo
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py <command> ...`.

Do not hand-generate IDs, status blocks, backlog records, or current-task records when `core/bin/guia.ps1` can do it.

## Where Behavior Lives

The per-verb action playbook is in each verb's shim body, which composes shared partials:

- `_partials/title_context_rules.md` — how to synthesize `<title>` vs `<context>` (feature, bug, chore, backlog).
- `_partials/post_cli.agent.md` / `_partials/post_cli.claude.md` — post-CLI flow per host (read `.guia/current-task.json`, repeat `NOME DO CHAT`, rename chat). The host-aware include `{{include_per_target: _partials/post_cli}}` in each verb body picks the right one at build time.
- `_partials/lock_protocol.md` — `features/registry.yaml` enforcement and unlock request flow (used by any verb that edits files).

Editing a partial changes every shim that uses it. This skill (`guia-fluxo`) is intentionally **not** part of that action chain — it stays as reference.

## Tool Notes per Host

- **Codex** does not treat arbitrary `/feature` or `/finish` as custom slash commands in every surface. Reliable Codex calls are direct script commands, `/use guia-fluxo`, or shim skills such as `$finish` after skills reload.
- **Antigravity** reads skills from the same `dist/.agents/skills/` tree as Codex. The shim skills in this pack work for both surfaces; treat any verb listed above as a callable workflow. No thread-rename API available — chat title falls back to printed text.
- **Claude Code** reads this pack as an official plugin: `dist/.claude-plugin/plugin.json` (name `guia`) exposes the skills in `dist/skills/<verb>/SKILL.md` under namespace `guia`. Shortcuts in Claude become `/guia:feature`, `/guia:bug`, `/guia:chore`, `/guia:backlog`, `/guia:promote`, `/guia:ready`, `/guia:finish`, `/guia:status`. Claude also auto-loads skills by description. All bodies are generated from `core/manifest/manifest.yaml`.

## Chat Rename per Host

- **Codex App:** call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the exact title printed after `NOME DO CHAT:`. The print alone does not rename the UI.
- **Claude Code:** call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the suggested title — reliable surrogate that places a divider + ToC entry in the transcript. Also try `/rename <suggested-title>` if the slash command is exposed in this build. `claude -n <title>` only works when starting a new session. Do not use Codex App `codex_app.*` tools in Claude.
- **Any host without a rename API:** print the suggested title and keep working.

If shell access fails, surface the exact command the developer can run by hand.

## Portable install

To reuse the pack in another project, copy:

- `.guia/process.json`
- `core/src/guia.py`
- `core/bin/guia.ps1`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/` (including `_partials/`)
- `core/build/render-skills.py`
- `core/lock/check-lock.py`
- `core/hooks/commit-msg`
- `dist/.claude-plugin/plugin.json` + `dist/.claude-plugin/marketplace.json`
- the generated `dist/.agents/skills/*` and `dist/skills/*` trees

Then run:

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```

To regenerate the per-agent files after editing the manifest or partials:

```powershell
python core/build/render-skills.py
```
