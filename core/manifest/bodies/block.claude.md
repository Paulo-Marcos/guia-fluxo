# Block

**Pausa a task atual com motivo obrigatorio.** Move o status para `Bloqueada`, preserva o WIP e mantem a entrada em `FEATURES.md`. Use para parar temporariamente: dependencia externa, espera por decisao, prioridade trocada. Distinto de `cancel` (terminal, nao volta) e `finish` (concluida).

Run:

```powershell
.\core\bin\ai.ps1 block $ARGUMENTS --reason "Por que esta pausando"
```

O `--reason` e **obrigatorio** (fica registrado em `task.blocks[]` para auditoria de tempo bloqueado).

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`) ou ja em `Bloqueada`.

Para retomar: `.\core\bin\ai.ps1 unblock <id>`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py block $ARGUMENTS --reason "..."`.

Depois repita a linha `NOME DO CHAT: ...` (vira `#BLOQUEADA`) e rode `/rename <suggested-title>` se a sessao expor essa API.
