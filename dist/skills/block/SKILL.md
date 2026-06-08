---
name: block
description: PAUSE in-flight task — preserva WIP, move status para `Bloqueada`. Triggered by /block or "$block" / "pausar tarefa / bloquear / esperar dependencia". Exige `--reason` obrigatorio (fica em `task.blocks[]`). Use quando a task vai voltar: esperando decisao, dependencia externa, prioridade trocada. Do NOT use for: encerramento definitivo (use $cancel), entrega para validacao (use $ready), ou fechamento (use $finish).
---

# Block

**Pause the current task with a mandatory reason.** Moves status to `Bloqueada`, preserves the WIP, and keeps the entry in `FEATURES.md`. Use to stop temporarily: external dependency, waiting on a decision, priority swap. Distinct from `cancel` (terminal, does not return) and `finish` (validated and closed).

Run:

```powershell
.\core\bin\guia.ps1 block <D-NNN> --reason "Why pausing"
```

`--reason` is **required** (recorded in `task.blocks[]` for blocked-time auditing).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already in `Bloqueada`.

To resume: `.\core\bin\guia.ps1 unblock <D-NNN>`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py block <D-NNN> --reason "..."`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.
