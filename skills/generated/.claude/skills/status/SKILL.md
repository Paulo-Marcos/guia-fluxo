---
name: status
description: Shim for ai-process. Use when the user invokes $status or asks for the current process task/status/title.
---

# Status

Show current AI-process task and suggested chat title.

Run:

```powershell
.\scripts\ai.ps1 status $ARGUMENTS
```

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
