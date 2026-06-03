---
name: issue
description: PRIMARY TRIGGER for /issue or "$issue". Creates a NEW I-NNN bug/regression task and starts the fix immediately. Do NOT use for: new features or net-new functionality (use $feature), deferred bug ideas (use $backlog), or evaluating an existing B-NNN (use $promote).
---

# Issue

Create a new issue or regression task before editing code.

Run:

```powershell
.\core\bin\ai.ps1 issue "$ARGUMENTS"
```

Useful flags: `--context "<observed failure>"`, `--origin "<source>"`.

Then read `.ai/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the fix.
