---
name: guia-cancel
description: TERMINAL CANCEL — closes the task with `status=Cancelada` (terminal, does not return). Use when the task will NOT be completed: created by mistake, scope dropped, wrong promote. Required: `--reason "<motive>"`. Options: `--keep-worktree` (default removes the worktree if present), `--set-current` (default clears current-task.json if the cancelled task was current). For a temporary pause that will resume use `block`; for a validated close use `finish`.
---

# Cancel

**Trigger by you (the agent) or the user, when the task will NOT be completed.** Marks the task as `Cancelada` (terminal) with a mandatory reason. Distinct from `block` (pause, will resume) and `finish` (validated and closed).

Typical cases:
- Demanda criada por engano.
- `promote` errado de um item de backlog.
- Mudanca de escopo: o que parecia uma feature/bug nao se justifica mais.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
cancel <D-NNN> --reason "Motivo curto"
```

`--reason` is **required** (justification stays in history under `task.cancellations[]` and in `FEATURES.md`).

Useful flags:
- `--keep-worktree`: do not remove the associated worktree (default: remove if present).
- `--set-current`: keep the task as current after canceling (default: clear `.guia/current-task.json` if the canceled task was current).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
