---
name: ready
description: HANDOFF to developer validation — does NOT close the task. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress F-NNN/I-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready

Move the current task to developer validation without finalizing it.

Run:

```powershell
.\scripts\ai.ps1 ready $ARGUMENTS
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and manual gaps with `--pending`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
