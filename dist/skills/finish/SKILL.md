---
name: finish
description: CLOSE an ALREADY-validated task; runs the docs-check hook, commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish

Finish the current task after developer validation.

## 1) Docs hook (mandatory when `.ai/docs-map.yaml` exists)

Run the docs check before closing:

```powershell
.\core\bin\ai.ps1 docs-check
```

For each candidate listed:

- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.ai/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Close

```powershell
.\core\bin\ai.ps1 finish $ARGUMENTS --docs-touched <path1> --docs-touched <path2>
```

Or, when no doc needed to change:

```powershell
.\core\bin\ai.ps1 finish $ARGUMENTS --docs-skip "<short reason>"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and use `--lock --lock-id <slug>` only when the developer asks to lock the finalized files. Use `--no-commit` for dry close.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py finish $ARGUMENTS --docs-skip "..."`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
