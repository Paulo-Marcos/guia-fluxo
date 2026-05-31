---
name: issue
description: PRIMARY TRIGGER for /issue or "$issue". Creates a NEW I-NNN bug/regression task and starts the fix immediately. Do NOT use for: new features or net-new functionality (use $feature), deferred bug ideas (use $backlog), or evaluating an existing B-NNN (use $promote).
---

# Issue Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 issue "<title>" --context "<context>"
```

Then continue using `ai-process`.
