---
name: guia-ready
description: HANDOFF to developer validation — does NOT close the task. THE AGENT runs this when implementation is finished, NOT the human; it is the gate that forces human-in-the-loop before $finish. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress D-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready Shim

**You (the agent) call this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish`.

Call the core process script:

```powershell
.\core\bin\guia.ps1 ready F-000 --file path/to/file --summary "What changed" --validation "What passed"
```

Then continue using `guia-fluxo`.
