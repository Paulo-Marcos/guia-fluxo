---
name: ready
description: Shim for ai-process. Use when the user invokes $ready or asks to send the current task to developer validation.
---

# Ready

Move the current task to developer validation without finalizing it.

Run:

```powershell
.\scripts\ai.ps1 ready $ARGUMENTS
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and manual gaps with `--pending`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
