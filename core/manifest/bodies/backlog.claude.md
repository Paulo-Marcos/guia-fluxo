# Backlog

Manage future work without starting implementation.

{{include: _partials/title_context_rules.md}}

If the user provided a title, run:

```powershell
.\core\bin\guia.ps1 backlog add "$ARGUMENTS"
```

If the user asks to list backlog, run:

```powershell
.\core\bin\guia.ps1 backlog list
```

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py backlog add|list "$ARGUMENTS"`.

{{include: _partials/post_cli.claude.md}}

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
