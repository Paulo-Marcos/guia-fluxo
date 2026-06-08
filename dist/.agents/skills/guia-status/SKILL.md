---
name: guia-status
description: READ-ONLY: show the current active task and the suggested chat title. Triggered by /status or "$status" / "qual a tarefa atual / status do processo". Never creates, modifies, advances, or closes a task. Do NOT use for: creating tasks (use $feature, $bug or $chore), handoff to validation (use $ready), or closing a validated task (use $finish).
---

# Status

Show the current Guia Fluxo task and the suggested chat title. Read-only — never mutates state.

Run:

```powershell
.\core\bin\guia.ps1 status
```

Or pass a specific task id:

```powershell
.\core\bin\guia.ps1 status <D-NNN>
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py status [<D-NNN>]`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
