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

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py backlog add|list "$ARGUMENTS"`.
