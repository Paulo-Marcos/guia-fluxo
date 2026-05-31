---
name: feature
description: Shim for ai-process. Use when the user invokes $feature or asks to start/register a new feature.
---

# Feature

Create a new feature task before editing code.

Run:

```powershell
.\scripts\ai.ps1 feature "$ARGUMENTS"
```

Then read `.ai/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the implementation.
