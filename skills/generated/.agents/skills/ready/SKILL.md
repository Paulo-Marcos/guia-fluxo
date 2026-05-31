---
name: ready
description: Shim for ai-process. Use when the user invokes $ready or asks to send the current task to developer validation.
---

# Ready Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 ready F-000 --file path/to/file --summary "What changed" --validation "What passed"
```

Then continue using `ai-process`.
