---
name: guia-start
description: START — comeca trabalho em uma task Planejada ou diretamente Backlog (status -> Em desenvolvimento). Triggered by /start or "$start" / "comecar tarefa / iniciar trabalho / bora codar". Diferente de $promote: assume triagem feita (kind ja decidido). Falha se task ja Em desenvolvimento ou terminal. Do NOT use for: criar nova task do zero (use $feature, $bug ou $chore), triar backlog item (use $promote), ou retomar pausa (use $unblock).
---

# Start

**Start work on a Planejada task (or directly from the Backlog).** Moves status to `Em desenvolvimento`. Assumes triage (kind = feature/bug/chore) is done — if you still need to decide the kind, use `$promote`.

Run:

```powershell
.\core\bin\guia.ps1 start <D-NNN> [--note "Starting now because..."]
```

Distinct from:
- `$promote <B-NNN>`: triage a backlog item deciding kind and plan before starting.
- `$plan`: mark as triaged without starting.
- `$feature/$bug/$chore` (new tasks): create a fresh task already `Em desenvolvimento`.

Accepts transition from `Backlog` (shortcut that skips `Planejada`) or `Planejada`. Fails if the task is already `Em desenvolvimento`, in a terminal state (`Validada`, `Finalizada`, `Cancelada`), or `Bloqueada` (use `$unblock`).

Tasks promoted from `Backlog` enter `FEATURES.md`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py start <D-NNN>`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
