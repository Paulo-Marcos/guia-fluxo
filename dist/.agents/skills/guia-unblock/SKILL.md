---
name: guia-unblock
description: RESUME a paused task — move status de `Bloqueada` para `Em desenvolvimento`. Triggered by /unblock or "$unblock" / "retomar tarefa / desbloquear / dependencia resolvida". Inverso de $block. Falha se a task nao estava em `Bloqueada`. Do NOT use for: criar nova task (use $feature, $bug ou $chore), promover backlog (use $promote), ou voltar de cancelamento (cancelamento e terminal - abra nova task).
---

# Unblock

**Resume a paused task.** Moves status from `Bloqueada` back to `Em desenvolvimento`. Use after `block` once the dependency/decision blocking the work has been resolved.

Run:

```powershell
.\core\bin\guia.ps1 unblock <D-NNN> [--note "What unblocked it"]
```

`--note` is optional — useful when it is worth recording what unblocked it (decision made, dependency resolved).

Fails if the task was not in `Bloqueada` (preserves the flow states).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py unblock <D-NNN>`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
