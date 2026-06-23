---
name: guia-start
description: START — begin work on a `Planejada` or `Backlog` task (status → `Em desenvolvimento`). Assumes triage is done (kind already decided); use `promote` when kind still needs deciding. Options: `--note "<starting note>"`. To resume from `Bloqueada` use `unblock`; to create a fresh task use `feature`/`bug`/`chore`.
---

# Start

**Start work on a Planejada task (or directly from the Backlog).** Moves status to `Em desenvolvimento`. Assumes triage (kind = feature/bug/chore) is done — if you still need to decide the kind, use `$promote`.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
start <D-NNN> [--note "Starting now because..."]
```

Distinct from:
- `$promote <B-NNN>`: triage a backlog item deciding kind and plan before starting.
- `$plan`: mark as triaged without starting.
- `$feature/$bug/$chore` (new tasks): create a fresh task already `Em desenvolvimento`.

Accepts transition from `Backlog` (shortcut that skips `Planejada`) or `Planejada`. Fails if the task is already `Em desenvolvimento`, in a terminal state (`Validada`, `Finalizada`, `Cancelada`), or `Bloqueada` (use `$unblock`).

Tasks promoted from `Backlog` enter `.guia/DEMANDAS.md`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
