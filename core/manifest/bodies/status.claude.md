# Status

Show current AI-process task and suggested chat title.

Run:

```powershell
.\core\bin\ai.ps1 status $ARGUMENTS
```

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py status $ARGUMENTS`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
