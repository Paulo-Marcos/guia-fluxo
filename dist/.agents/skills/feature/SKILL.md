---
name: feature
description: PRIMARY TRIGGER for /feature or "$feature". Creates a NEW F-NNN feature task and starts implementation immediately. Do NOT use for: bugs/regressions (use $issue), deferred ideas without starting work (use $backlog), or evaluating an existing B-NNN (use $promote).
---

# Feature Shim

Call the core process script:

```powershell
.\core\bin\ai.ps1 feature "<title>" --context "<context>"
```

Then continue using `ai-process`.
