# Feature

Create a new feature task before editing code.

Run:

```powershell
.\core\bin\ai.ps1 feature "$ARGUMENTS"
```

Useful flags: `--context "<why>"` (motivacao), `--origin "<source>"` (origem alternativa).

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py feature "$ARGUMENTS"`.

Then read `.ai/current-task.json`, repeat the exact `NOME DO CHAT: ...` line, run `/rename <suggested-title>` if Claude supports it, and continue with the implementation.
