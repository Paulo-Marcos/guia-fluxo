---
name: backlog
description: DEFER-AND-PARK skill: never starts implementation. Triggered ONLY by /backlog or "$backlog" with a subcommand (add / list). Saves future ideas to .ai/backlog.json (B-NNN) or lists them. Do NOT use for: starting work now (use $feature for new functionality or $issue for bugs), or evaluating one specific B-NNN to convert it (use $promote).
---

# Backlog

Manage future work without starting implementation.

If the user provided a title, run:

```powershell
.\core\bin\ai.ps1 backlog add "$ARGUMENTS"
```

If the user asks to list backlog, run:

```powershell
.\core\bin\ai.ps1 backlog list
```
