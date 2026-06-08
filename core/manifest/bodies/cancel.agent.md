# Cancel Shim

Encerra uma task como `Cancelada` (terminal) com motivo obrigatorio. Use quando a demanda NAO sera concluida (criada por engano, escopo mudou, promote errado). Para pausar e voltar depois, use `block`/`unblock`.

Call the core process script:

```powershell
.\core\bin\guia.ps1 cancel F-000 --reason "Motivo curto" [--keep-worktree] [--set-current]
```

- `--reason` e obrigatorio.
- Sem `--keep-worktree`, a worktree associada (se houver) e removida.
- Sem `--set-current`, o `.guia/current-task.json` e limpo se apontava para a task cancelada.

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`).

Depois continue usando `guia-fluxo`.
