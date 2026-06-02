---
name: status
description: READ-ONLY: show the current active task and the suggested chat title. Triggered by /status or "$status" / "qual a tarefa atual / status do processo". Never creates, modifies, advances, or closes a task. Do NOT use for: creating tasks (use $feature or $issue), handoff to validation (use $ready), or closing a validated task (use $finish).
---

# Status

Show current AI-process task and suggested chat title.

Run:

```powershell
.\core\bin\ai.ps1 status $ARGUMENTS
```

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
