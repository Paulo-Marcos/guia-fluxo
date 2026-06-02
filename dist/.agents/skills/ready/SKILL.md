---
name: ready
description: HANDOFF to developer validation — does NOT close the task. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress F-NNN/I-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready Shim

Call the core process script:

```powershell
.\core\bin\ai.ps1 ready F-000 --file path/to/file --summary "What changed" --validation "What passed"
```

Then continue using `ai-process`.
