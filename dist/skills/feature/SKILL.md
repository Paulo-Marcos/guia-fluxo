---
name: feature
description: PRIMARY TRIGGER for /feature or "$feature". Creates a NEW D-NNN feature task and starts implementation immediately. Do NOT use for: bugs/regressions (use $bug), maintenance without behavior change (use $chore), deferred ideas without starting work (use $backlog), or evaluating an existing B-NNN (use $promote).
---

# Feature

Create a new feature task before editing code.

Run:

```powershell
.\core\bin\guia.ps1 feature "$ARGUMENTS"
```

Useful flags: `--context "<why>"` (motivacao), `--origin "<source>"` (origem alternativa).

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py feature "$ARGUMENTS"`.

Then read `.guia/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the implementation.
