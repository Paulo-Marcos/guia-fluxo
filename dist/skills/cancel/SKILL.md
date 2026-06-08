---
name: cancel
description: TERMINAL CANCEL — encerra a task com `status: Cancelada` (terminal, nao volta). Triggered by /cancel or "$cancel" / "cancelar tarefa / nao vou fazer / criada por engano". Exige `--reason` obrigatorio. Use para: demanda criada por engano, promote errado, escopo desfeito. Do NOT use for: pausa temporaria que vai voltar (use $block), tarefa concluida e validada (use $finish), ou re-triagem (cancele e abra nova).
---

# Cancel

**Trigger by you (the agent) or the user, when the task will NOT be completed.** Marks the task as `Cancelada` (terminal) with a mandatory reason. Distinct from `block` (pause, will resume) and `finish` (validated and closed).

Typical cases:
- Demanda criada por engano.
- `promote` errado de um item de backlog.
- Mudanca de escopo: o que parecia uma feature/bug nao se justifica mais.

Run:

```powershell
.\core\bin\guia.ps1 cancel <D-NNN> --reason "Motivo curto"
```

`--reason` is **required** (justification stays in history under `task.cancellations[]` and in `FEATURES.md`).

Useful flags:
- `--keep-worktree`: do not remove the associated worktree (default: remove if present).
- `--set-current`: keep the task as current after canceling (default: clear `.guia/current-task.json` if the canceled task was current).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py cancel <D-NNN> --reason "..."`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
