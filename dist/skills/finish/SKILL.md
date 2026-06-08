---
name: finish
description: CLOSE an ALREADY-validated task; runs the docs-check hook, commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish

Finish the current task after developer validation.

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```powershell
.\core\bin\guia.ps1 docs-check
```

For each candidate listed:

- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.guia/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Close

```powershell
.\core\bin\guia.ps1 finish $ARGUMENTS --docs-touched <path1> --docs-touched <path2>
```

Or, when no doc needed to change:

```powershell
.\core\bin\guia.ps1 finish $ARGUMENTS --docs-skip "<short reason>"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and use `--lock --lock-id <slug>` only when the developer asks to lock the finalized files. Use `--no-commit` for dry close.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py finish $ARGUMENTS --docs-skip "..."`.

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

Task is closed.
