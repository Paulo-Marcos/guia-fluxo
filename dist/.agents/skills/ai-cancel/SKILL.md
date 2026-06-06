---
name: ai-cancel
description: TERMINAL CANCEL — encerra a task com `status: Cancelada` (terminal, nao volta). Triggered by /cancel or "$cancel" / "cancelar tarefa / nao vou fazer / criada por engano". Exige `--reason` obrigatorio. Use para: demanda criada por engano, promote errado, escopo desfeito. Do NOT use for: pausa temporaria que vai voltar (use $block), tarefa concluida e validada (use $finish), ou re-triagem (cancele e abra nova).
---

# Cancel Shim

Encerra uma task como `Cancelada` (terminal) com motivo obrigatorio. Use quando a demanda NAO sera concluida (criada por engano, escopo mudou, promote errado). Para pausar e voltar depois, use `block`/`unblock`.

Call the core process script:

```powershell
.\core\bin\ai.ps1 cancel F-000 --reason "Motivo curto" [--keep-worktree] [--set-current]
```

- `--reason` e obrigatorio.
- Sem `--keep-worktree`, a worktree associada (se houver) e removida.
- Sem `--set-current`, o `.ai/current-task.json` e limpo se apontava para a task cancelada.

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`).

Depois continue usando `ai-process`.
