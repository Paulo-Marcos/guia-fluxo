---
name: bug
description: PRIMARY TRIGGER for /bug or "$bug". Creates a NEW D-NNN bug/regression task with kind=bug (substitui o antigo /issue removido na Fase 4 do ADR-0011). Use para defeitos, regressoes e comportamento incorreto. Do NOT use for: nova capacidade (use $feature), manutencao sem mudanca de comportamento (use $chore), ideia parqueada (use $backlog) ou avaliar um B-NNN existente (use $promote).
---

# Bug

Cria uma task de bug (regressao, defeito, comportamento incorreto) antes de editar codigo. Substitui o antigo `/issue` (removido na Fase 4 do ADR-0011 — `issue` colidia com o sentido guarda-chuva do termo em GitHub/Jira/Linear).

## Title vs Context

When the human asks in loose phrasing, **synthesize** — do not pass the raw sentence to the CLI.

- `<title>`: short imperative, 5–8 words, ≤60 chars. Captures the *what*. Title is what shows in `NOME DO CHAT` and in task lists.
- `<context>`: full motivation, scenario, success criteria. Captures the *why*. Multi-line allowed. Goes into `task.context`, `FEATURES.md`, and search.

Example:

> Human: "queria que o /finish mostrasse o tempo total da task"
>
> → title:   `Show total task time on /finish`
> → context: `User wants /finish to print elapsed time since task creation so they can see how long the work took without opening JSON.`

If the human-provided phrasing already reads as an imperative under 60 chars, use it as-is. Synthesis is for loose/long phrasings, not a mandatory rewrite.

Run:

```powershell
.\core\bin\guia.ps1 bug "$ARGUMENTS"
```

Flags uteis:
- `--context "<sintoma + impacto>"` — comportamento observado vs esperado, quem foi atingido.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` se ainda nao triado, `planned` se ja sabe que vai mexer mas nao agora.
- `--origin "<source>"` — origem alternativa.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py bug "$ARGUMENTS"`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

## File locks

Before editing files, honor `features/registry.yaml`. If a target file is locked:

1. **Stop** before the edit.
2. **Explain to the developer**, in this order:
   - The lock id and which functionality it protects.
   - Why the planned edit is needed.
   - Expected impact (what changes, who notices).
   - Regression risk (what could break that is currently working).
   - Alternatives (route the change through a different file, scope reduction, etc.).
3. **Ask** for explicit authorization to proceed (or to unlock).
4. Only after the developer authorizes, edit — or use `python core/lock/check-lock.py unlock <id>` if the developer asks for the lock to be removed.

Never bypass a lock silently. The hook at commit time will reject the commit anyway, and the developer loses trust if the agent treats locks as advisory.

Then continue with the investigation and fix.
