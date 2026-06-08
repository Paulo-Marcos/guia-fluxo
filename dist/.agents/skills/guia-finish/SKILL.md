---
name: guia-finish
description: CLOSE an ALREADY-validated task; runs the docs-check hook, commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish Shim

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```powershell
.\core\bin\guia.ps1 docs-check
```

For each listed candidate, open the doc, decide if it needs an update, edit it when it does. If `.guia/docs-map.yaml` does not exist the project has no docs control and the hook is a no-op.

## 2) Close

```powershell
.\core\bin\guia.ps1 finish D-000 --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
.\core\bin\guia.ps1 finish D-000 --docs-skip "fluxo interno, sem mudanca user-facing"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

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

Task is closed. Continue using `guia-fluxo` only if the developer starts another task in this same conversation.
