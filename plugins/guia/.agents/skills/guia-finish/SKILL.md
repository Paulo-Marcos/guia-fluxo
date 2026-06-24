---
name: guia-finish
description: CLOSE an already-validated task — runs the docs-check hook and commits by default. **Requires the developer's prior authorization (technical gate, D-080): env `GUIA_HUMAN_FINISH=1` set in the session, else the tool refuses. An AI agent must not set this env itself — it is the developer's signal; stop at `ready` and hand off, and only run `finish` when the developer already authorized it.** Use only after the developer confirms validation in real use. Required when `.guia/docs-map.yaml` exists: `--docs-touched <path>` (repeatable) or `--docs-skip "<reason>"`. Options: `--file`, `--summary`, `--validation` (same as ready), `--no-commit` (dry close), `--lock --lock-id <slug> --lock-description "..."` (protect files after close). For handoff to validation use `ready`; for inspection use `status`.
---

# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **Human authorization required (technical gate, D-080).** `finish` is the developer's call. The tool now **refuses** to close unless the developer pre-authorized it via the `GUIA_HUMAN_FINISH=1` env var set in their session. **If you are an AI agent, your job ends at `ready` — do NOT set this env var yourself; it is the developer's signal.** When the developer has already given prior authorization (the env is set in the session), `finish` may run; otherwise stop at `ready` and hand off.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```text
docs-check
```

For each listed candidate:
- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.guia/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Close

Requires the developer's prior authorization — the `GUIA_HUMAN_FINISH=1` env var set in the session (D-080), e.g. `$env:GUIA_HUMAN_FINISH = "1"` in PowerShell:

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

## File locks

Before editing files, honor `.guia/locks/registry.yaml`. If a target file is locked:

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

Task is closed.
