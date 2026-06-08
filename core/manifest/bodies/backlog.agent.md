# Backlog Shim

Manage parked work. `backlog add` creates a `D-NNN` task with `status=Backlog` (not started). `backlog list` shows all parked items (new D-NNN + legacy B-NNN). `backlog promote` delegates to the `/promote` flow.

{{include: _partials/title_context_rules.md}}

Call the core process script:

```powershell
.\core\bin\guia.ps1 backlog add "<title>" --context "<context>"
.\core\bin\guia.ps1 backlog list
.\core\bin\guia.ps1 backlog promote B-001
```

{{include: _partials/post_cli.agent.md}}

**Do not start implementation.** Backlog is the defer-and-park surface. To begin work on a parked item later, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
