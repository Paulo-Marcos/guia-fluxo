---
name: guia-fluxo
description: REFERENCE/BACKGROUND ONLY for the Guia Fluxo task-process pipeline (D-NNN/B-NNN, locks, chat-rename, worktree). Loaded as context by the dedicated shims, not as a trigger competitor. Do NOT auto-fire on /feature, /bug, /chore, /backlog, /promote, /ready, /finish, /status — those route to their own shims first. Use guia-fluxo directly ONLY when the user asks for the full process overview ("explain Guia Fluxo", "how does this pipeline work", "como funciona o guia-fluxo") or needs the installation/portability guide.
---

# Guia Fluxo

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

Rules:

1. Create or update the task before code edits.
2. Do not hand-generate IDs when `core/bin/guia.ps1` can do it.
3. After every phase command, repeat the exact `NOME DO CHAT: ...` line printed by the script.
4. Rename the real Claude chat/session when Claude exposes a supported path: use `/rename <suggested-title>` during the session, or start a new session with `claude -n <suggested-title>` when that flag is supported.
5. If Claude cannot rename from the agent turn, print the suggested title and keep working. Do not use Codex App `codex_app.*` tools in Claude.
6. Honor `features/registry.yaml` before file edits. If a file is locked, explain the lock id, protected functionality, why the edit is needed, expected impact, regression risk, and alternatives before asking for unlock.
7. Use `/promote <B-NNN>` to evaluate a backlog item before creating a task: classify feature/bug/chore, ask missing questions, propose plan, confront risks/locks, ask worktree yes/no, then run `.\core\bin\guia.ps1 promote ...` after user OK.
8. If user chooses worktree, pass `--worktree`; `finish` removes the created worktree when the task is closed.
9. Use `/ready` when implementation is done but still needs developer validation.
10. Use `/finish` only after the developer confirms final validation. It commits by default and suggests `#FINALIZADO`.
11. Use `--lock` only when the developer asks to create a lock.

Portable install:

```powershell
.\core\bin\guia.ps1 init --project-name "new-project"
```
