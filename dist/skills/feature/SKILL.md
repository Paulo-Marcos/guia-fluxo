---
name: feature
description: PRIMARY TRIGGER for /feature or "$feature". Creates a NEW F-NNN feature task and starts implementation immediately. Do NOT use for: bugs/regressions (use $issue), deferred ideas without starting work (use $backlog), or evaluating an existing B-NNN (use $promote).
---

# Feature

Create a new feature task before editing code.

Run:

```powershell
.\core\bin\ai.ps1 feature "$ARGUMENTS"
```

Useful flags: `--context "<why>"` (motivacao), `--origin "<source>"` (origem alternativa).

Then read `.ai/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the implementation.
