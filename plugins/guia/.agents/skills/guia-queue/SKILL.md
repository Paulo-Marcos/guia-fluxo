---
name: guia-queue
description: "QUEUE — show the merge queue (order, state, why each item waits; `--json`), put an audited PR in it (`add [D-NNN] [--priority hotfix]`, requires the approved audit on the current head; at level >= `queue` it enters approved unless something in `alwaysHuman` holds it), or bring labeled cloud PRs in (`import`). Agent may `add` at level >= `queue`. For pause/resume/remove/priority/run use `queue-control` (user-only); for the merge ok use `approve`."
---

# Queue

The chat launches (`ship` -> `audit` -> `queue add`) and is free; one executor integrates one PR at a time.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
queue                     # list, with the reason each item waits
queue add [D-NNN] [--priority hotfix]
queue import              # PRs labeled guia:fila from the cloud (no audit yet)
```

- If `add` prints `alwaysHuman: ...`, the item waits for the developer's `approve`: tell them the reason.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
