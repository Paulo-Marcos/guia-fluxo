---
name: plan
description: PLAN — marca task como `Planejada` (triada mas nao iniciada). Triggered by /plan or "$plan" / "planejar tarefa / triagem feita / aguardar para comecar". Aceita transicao de Backlog (item parqueado que ganhou prioridade) ou de Em desenvolvimento (despriorizado mas ja conhecido). Do NOT use for: comecar trabalho agora (use $start ou $promote), guardar ideia sem decidir (use $backlog), ou entregar pra validacao (use $ready).
---

# Plan

**Mark the task as `Planejada`** (triaged but not yet started). Use when you already know you will work on the task but not now — moves out of `Backlog` (parked) or back from `Em desenvolvimento` (deprioritized).

Run:

```powershell
.\core\bin\guia.ps1 plan <D-NNN> [--note "Why planning now"]
```

Distinct from:
- `$backlog add`: park an idea that has not been triaged yet.
- `$promote`: triage a legacy B-NNN deciding feature/bug and start immediately.
- `$start`: start now (moves from `Backlog` or `Planejada` to `Em desenvolvimento`).

Fails if the task is in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already `Planejada`. Tasks promoted from `Backlog` to `Planejada` enter `FEATURES.md` (join the catalog).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py plan <D-NNN>`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
