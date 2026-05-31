---
name: backlog
description: Shim for ai-process. Use when the user invokes $backlog or asks to add, list, or promote backlog items.
---

# Backlog Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 backlog add "<title>" --context "<context>"
.\scripts\ai.ps1 backlog list
.\scripts\ai.ps1 backlog promote B-001
```

Then continue using `ai-process`.
