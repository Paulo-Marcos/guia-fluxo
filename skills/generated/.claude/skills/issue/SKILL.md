---
name: issue
description: Shim for ai-process. Use when the user invokes $issue or asks to start/register a bug, issue, or regression.
---

# Issue

Create a new issue or regression task before editing code.

Run:

```powershell
.\scripts\ai.ps1 issue "$ARGUMENTS"
```

Then read `.ai/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the fix.
