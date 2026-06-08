# Backlog

Manage parked work without starting implementation. `backlog add` creates a `D-NNN` task with `status=Backlog`. `backlog list` shows all parked items (new D-NNN + legacy B-NNN). `backlog promote` delegates to the `/promote` flow.

{{include: _partials/title_context_rules.md}}

If the user provided a title, run:

```powershell
.\core\bin\guia.ps1 backlog add "<title>" --context "<context>"
```

To list parked work:

```powershell
.\core\bin\guia.ps1 backlog list
```

To promote a backlog item:

```powershell
.\core\bin\guia.ps1 backlog promote B-001
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py backlog add|list|promote ...`.

{{include_per_target: _partials/post_cli}}

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
