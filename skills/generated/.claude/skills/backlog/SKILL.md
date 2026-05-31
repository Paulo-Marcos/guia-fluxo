---
name: backlog
description: Shim for ai-process. Use when the user invokes $backlog or asks to add, list, or promote backlog items.
---

# Backlog

Manage future work without starting implementation.

If the user provided a title, run:

```powershell
.\scripts\ai.ps1 backlog add "$ARGUMENTS"
```

If the user asks to list backlog, run:

```powershell
.\scripts\ai.ps1 backlog list
```
