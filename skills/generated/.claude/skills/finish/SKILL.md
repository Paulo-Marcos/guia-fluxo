---
name: finish
description: CLOSE an ALREADY-validated task; commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish

Finish the current task after developer validation.

Run:

```powershell
.\scripts\ai.ps1 finish $ARGUMENTS
```

This marks the task as final, suggests `#FINALIZADO`, and commits by default. Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and use `--lock --lock-id <slug>` only when the developer asks to lock the finalized files. Use `--no-commit` for dry close.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
