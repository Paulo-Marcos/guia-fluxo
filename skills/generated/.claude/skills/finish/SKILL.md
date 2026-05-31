---
name: finish
description: Shim for ai-process. Use when the user invokes $finish or asks to finalize/close a validated feature or issue, commit it, and optionally lock it.
---

# Finish

Finish the current task after developer validation.

Run:

```powershell
.\scripts\ai.ps1 finish $ARGUMENTS
```

This marks the task as final, suggests `#FINALIZADO`, and commits by default. Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and use `--lock --lock-id <slug>` only when the developer asks to lock the finalized files. Use `--no-commit` for dry close.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
