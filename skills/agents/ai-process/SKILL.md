---
name: ai-process
description: Portable task-process skill for Codex, Claude, Antigravity, and other agents. Use when the user invokes /feature, /issue, /backlog, /promote, /ready, /finish, /status, asks to register a demand, create a feature/issue, promote backlog, manage backlog, hand off for validation, finish a validated task, lock a validated feature, or keep AI-agent work synchronized across tools.
---

# AI Process

Use this skill to run the repository process through deterministic scripts instead of hand-editing process files.

## Trigger Commands

- `/feature <title>`: create a new `F-NNN` task.
- `/issue <title>`: create a new `I-NNN` task.
- `/backlog add <title>`: save future work without starting implementation.
- `/backlog list`: show future work.
- `/backlog promote <B-NNN>`: convert backlog item into feature or issue.
- `/promote <B-NNN>`: AI evaluates backlog item, asks for missing information, proposes plan, asks worktree yes/no, then promotes it.
- `/status [F-NNN|I-NNN]`: show active task and suggested chat title.
- `/ready [F-NNN|I-NNN]`: mark implementation as waiting for developer validation.
- `/finish [F-NNN|I-NNN]`: close an already validated task, suggest `#FINALIZADO`, and commit by default.

## Core Rule

Run `scripts/ai.ps1` or `scripts/ai.py`. Do not manually create IDs, status blocks, backlog records, or current-task records when the script can do it.

Preferred Windows commands:

```powershell
.\scripts\ai.ps1 feature "Short title" --context "Why this matters"
.\scripts\ai.ps1 issue "Bug title" --context "Observed failure"
.\scripts\ai.ps1 backlog add "Future idea" --context "Useful later"
.\scripts\ai.ps1 promote B-001 --kind feature --assessment "Clear feature" --plan "Inspect affected files"
.\scripts\ai.ps1 status
.\scripts\ai.ps1 ready F-016 --file scripts/ai.py --summary "Implemented process CLI"
.\scripts\ai.ps1 finish F-016 --lock --lock-id ai-process-pack
```

Portable fallback:

```bash
python scripts/ai.py feature "Short title" --context "Why this matters"
```

## Agent Behavior

1. On `/feature` or `/issue`, create the task before code edits.
2. Read `.ai/current-task.json` before continuing implementation.
3. After every phase command, repeat the exact line printed by the script:
   - `NOME DO CHAT: F-016 - #DEV - Example title`
   - `NOME DO CHAT: F-016 - #VALIDACAO - Example title`
   - `NOME DO CHAT: F-016 - #FINALIZADO - Example title`
4. Rename the real chat/session, not only the visible message, whenever the host exposes a supported thread/session API.
5. In Codex App, search for the thread tools if needed, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with exactly the title printed after `NOME DO CHAT:`.
6. If no thread API is available, use that title as best-effort chat title:
   - `F-016 - #DEV - Example title`
   - `F-016 - #VALIDACAO - Example title`
   - `F-016 - #FINALIZADO - Example title`
7. Before editing files, honor `features/registry.yaml` locks.
8. If a needed file is locked, explain the lock id, protected functionality, why the edit is needed, expected impact, regression risk, and alternatives before asking for unlock.
9. On `/promote <B-NNN>`, read the backlog item first. Decide issue vs feature, check if the request is actionable, ask missing questions if needed, propose a short execution plan, confront risks/locks, and ask whether to use worktree. Only after user OK, run `scripts/ai.ps1 promote ...`.
10. If user chooses worktree, pass `--worktree`; the task stores worktree metadata and `finish` removes it when closing.
11. On `/ready`, register changed files, summary, validations, and pending manual validation.
12. On `/finish`, only close when the developer says the work is validated/final. Commit is on by default; pass `--no-commit` for dry close.
13. Use `--lock` on `/finish` only when the developer asks to create/update the lock.

## Tool Notes

- Codex does not treat arbitrary `/feature` or `/finish` as custom slash commands in every surface. Reliable Codex calls are direct script commands, `/use ai-process`, or shim skills such as `$finish` after skills reload.
- Antigravity can expose plugin/skill workflows as slash commands.
- Claude can use `.claude/commands/*.md` as thin slash-command adapters.
- Codex App chat rename is explicit: printing `NOME DO CHAT: ...` does not rename the UI. Use `codex_app.list_threads` to find the current thread id and `codex_app.set_thread_title` with the exact suggested title. If those tools are not loaded, search for thread tools first.
- Claude chat rename: use `/rename <suggested-title>` when Claude Code exposes it, or start a session with `claude -n <suggested-title>` when that flag is supported. Claude does not use Codex App `codex_app.*` tools.
- If a host cannot rename from the agent turn, print the suggested title and keep working.
- If shell access fails, explain the exact command the developer can run.

## Portability

This skill is intentionally project-neutral. To reuse it elsewhere, copy:

- `.ai/process.json`
- `scripts/ai.py`
- `scripts/ai.ps1`
- `.agents/skills/ai-process/SKILL.md`
- `.claude/skills/ai-process/SKILL.md`
- `.claude/commands/*.md`

Then run:

```powershell
.\scripts\ai.ps1 init --project-name "new-project"
```
