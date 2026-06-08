---
name: backlog
description: DEFER-AND-PARK skill: never starts implementation. Triggered ONLY by /backlog or "$backlog" with a subcommand (add / list). Saves future ideas to .guia/backlog.json (B-NNN) or lists them. Do NOT use for: starting work now (use $feature for new functionality, $bug for regressions, or $chore for maintenance), or evaluating one specific B-NNN to convert it (use $promote).
---

# Backlog

Manage future work without starting implementation.

If the user provided a title, run:

```powershell
.\core\bin\guia.ps1 backlog add "$ARGUMENTS"
```

If the user asks to list backlog, run:

```powershell
.\core\bin\guia.ps1 backlog list
```

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py backlog add|list "$ARGUMENTS"`.
