# AI Process

Use repository scripts as the source of truth:

```powershell
.\core\bin\ai.ps1 feature "Short title" --context "Why this matters"
.\core\bin\ai.ps1 issue "Bug title" --context "Observed failure"
.\core\bin\ai.ps1 backlog add "Future idea" --context "Useful later"
.\core\bin\ai.ps1 promote B-001 --kind feature --assessment "Clear feature" --plan "Inspect affected files"
.\core\bin\ai.ps1 status
.\core\bin\ai.ps1 ready F-016 --file core/src/ai.py --summary "Implemented process CLI"
.\core\bin\ai.ps1 finish F-016 --lock --lock-id ai-process-pack
```

Rules:

1. Create or update the task before code edits.
2. Do not hand-generate IDs when `core/bin/ai.ps1` can do it.
3. After every phase command, repeat the exact `NOME DO CHAT: ...` line printed by the script.
4. Rename the real Claude chat/session when Claude exposes a supported path: use `/rename <suggested-title>` during the session, or start a new session with `claude -n <suggested-title>` when that flag is supported.
5. If Claude cannot rename from the agent turn, print the suggested title and keep working. Do not use Codex App `codex_app.*` tools in Claude.
6. Honor `features/registry.yaml` before file edits. If a file is locked, explain the lock id, protected functionality, why the edit is needed, expected impact, regression risk, and alternatives before asking for unlock.
7. Use `/promote <B-NNN>` to evaluate a backlog item before creating a task: classify feature/issue, ask missing questions, propose plan, confront risks/locks, ask worktree yes/no, then run `.\core\bin\ai.ps1 promote ...` after user OK.
8. If user chooses worktree, pass `--worktree`; `finish` removes the created worktree when the task is closed.
9. Use `/ready` when implementation is done but still needs developer validation.
10. Use `/finish` only after the developer confirms final validation. It commits by default and suggests `#FINALIZADO`.
11. Use `--lock` only when the developer asks to create a lock.

Portable install:

```powershell
.\core\bin\ai.ps1 init --project-name "new-project"
```
