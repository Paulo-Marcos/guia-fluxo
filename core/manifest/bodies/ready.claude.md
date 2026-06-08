# Ready

**Quem dispara este verbo: a IA, ao terminar de codar.** Nao e o humano avisando que vai validar. `ready` e o handoff que sinaliza "implementacao concluida, aguardando validacao humana em uso real". O proprio nome do estado e `Aguardando validacao`. Fluxo: IA implementa -> IA roda `ready` -> humano valida -> IA roda `finish`. Nao pule o `ready` indo direto pro `finish`: ele e o gate que forca human-in-the-loop (`validate` foi depreciado em F-003 justamente por isso).

Move the current task to developer validation without finalizing it.

Run:

```powershell
.\core\bin\guia.ps1 ready $ARGUMENTS
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands with `--validation`, and manual gaps with `--pending`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py ready $ARGUMENTS`.

Then repeat the exact `NOME DO CHAT: ...` line and run `/rename <suggested-title>` if Claude supports it.
