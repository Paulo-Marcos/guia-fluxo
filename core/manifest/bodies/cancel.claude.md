# Cancel

**Quem dispara este verbo: voce (IA) ou o usuario, quando a task NAO vai ser concluida.** Marca a task como `Cancelada` (terminal) com um motivo obrigatorio. Distinto de `block` (pausa, vai voltar) e `finish` (concluida e validada).

Casos tipicos:
- Demanda criada por engano.
- `promote` errado de um item de backlog.
- Mudanca de escopo: o que parecia uma feature/issue nao se justifica mais.

Run:

```powershell
.\core\bin\guia.ps1 cancel $ARGUMENTS --reason "Motivo curto"
```

O `--reason` e **obrigatorio** (justificativa fica no historico em `task.cancellations[]` e em `FEATURES.md`).

Flags uteis:

- `--keep-worktree`: nao remove a worktree associada (default: remove se existir e o cancel for explicito).
- `--set-current`: mantem a task como current apos cancelar (default: limpa `.guia/current-task.json` se a task cancelada era a current).

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`).

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py cancel $ARGUMENTS --reason "..."`.

Depois repita a linha `NOME DO CHAT: ...` e rode `/rename <suggested-title>` se a sessao expor essa API.
