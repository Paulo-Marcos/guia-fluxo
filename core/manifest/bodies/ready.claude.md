# Ready

Move the current task to developer validation without finalizing it.

Run:

```powershell
.\core\bin\ai.ps1 ready $ARGUMENTS
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and manual gaps with `--pending`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py ready $ARGUMENTS`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
