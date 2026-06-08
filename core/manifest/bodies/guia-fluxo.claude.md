# Guia Fluxo

Reference for the repository's task-process pipeline. Use this skill when the developer wants the **process overview** — what verbs exist, who triggers what, how the moving parts fit. The action playbook for each verb lives in the verb's own shim plus shared partials in `core/manifest/bodies/_partials/`.

## Trigger Commands

Legend: 👤 human triggers | 🤖 agent triggers | 👤→🤖 human authorizes, agent executes.

- 👤 `/guia:feature <title>`: create a new `D-NNN` feature task.
- 👤 `/guia:bug <title>`: create a new `D-NNN` bug task.
- 👤 `/guia:chore <title>`: create a new `D-NNN` chore task.
- 👤 `/guia:backlog add <title>`: park future work without starting implementation.
- 👤 `/guia:backlog list`: show parked work.
- 👤 `/guia:promote <B-NNN>`: agent evaluates the backlog item, proposes plan, asks worktree yes/no, then promotes it after the developer OKs.
- 👤 `/guia:status [D-NNN]`: show active task and suggested chat title.
- 🤖 `/guia:ready [D-NNN]`: handoff to validation. **The agent itself runs this when implementation ends** — never the human, never as a shortcut to skip ahead to `/guia:finish`.
- 👤→🤖 `/guia:finish [D-NNN]`: close an already-validated task. The human confirms validation in real use; the agent runs the command.

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

Do not hand-generate IDs, status blocks, backlog records, or current-task records when `core/bin/guia.ps1` can do it.

## Where Behavior Lives

The per-verb action playbook is in each verb's shim body, which composes shared partials:

- `_partials/title_context_rules.md` — how to synthesize `<title>` vs `<context>` (feature, bug, chore, backlog).
- `_partials/post_cli.claude.md` — post-CLI flow: read `.guia/current-task.json`, repeat `NOME DO CHAT`, call `mark_chapter` as the reliable rename surrogate in Claude Code, also try `/rename <suggested-title>` when the build exposes it.
- `_partials/lock_protocol.md` — `features/registry.yaml` enforcement and unlock request flow (any verb that edits files).

Editing a partial changes every shim that uses it. This skill (`guia-fluxo`) is intentionally **not** part of that action chain — it stays as reference.

## Chat Rename in Claude Code

Claude Code does not expose a stable agent-driven rename of the chat sidebar title. The **reliable surrogate** is `mark_chapter` (`mcp__ccd_session__mark_chapter`): it drops a visible divider in the transcript and a ToC entry the developer can jump to. Call it on every phase transition (`#DEV` at creation, `#VALIDACAO` at ready, `#FINALIZADO` at finish) with the exact title printed after `NOME DO CHAT:`. Also try `/rename <suggested-title>` — if the slash command is exposed in this build, the sidebar also renames; if not, the chapter marker still solves the navigation need.

Do not use Codex App `codex_app.*` tools in Claude.

## Portable install

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```

To regenerate the per-agent files after editing the manifest or partials:

```powershell
python core/build/render-skills.py
```
