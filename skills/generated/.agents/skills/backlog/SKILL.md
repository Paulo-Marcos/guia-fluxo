---
name: backlog
description: DEFER-AND-PARK skill: never starts implementation. Triggered ONLY by /backlog or "$backlog" with a subcommand (add / list). Saves future ideas to .ai/backlog.json (B-NNN) or lists them. Do NOT use for: starting work now (use $feature for new functionality or $issue for bugs), or evaluating one specific B-NNN to convert it (use $promote).
---

# Backlog Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 backlog add "<title>" --context "<context>"
.\scripts\ai.ps1 backlog list
.\scripts\ai.ps1 backlog promote B-001
```

Then continue using `ai-process`.
