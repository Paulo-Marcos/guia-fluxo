---
name: guia-status
description: READ-ONLY: show the current active task and the suggested chat title. Triggered by /status or "$status" / "qual a tarefa atual / status do processo". Never creates, modifies, advances, or closes a task. Do NOT use for: creating tasks (use $feature, $bug or $chore), handoff to validation (use $ready), or closing a validated task (use $finish).
---

# Status Shim

Call the core process script:

```powershell
.\core\bin\guia.ps1 status
```
