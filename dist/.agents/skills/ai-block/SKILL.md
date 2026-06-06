---
name: ai-block
description: PAUSE in-flight task — preserva WIP, move status para `Bloqueada`. Triggered by /block or "$block" / "pausar tarefa / bloquear / esperar dependencia". Exige `--reason` obrigatorio (fica em `task.blocks[]`). Use quando a task vai voltar: esperando decisao, dependencia externa, prioridade trocada. Do NOT use for: encerramento definitivo (use $cancel), entrega para validacao (use $ready), ou fechamento (use $finish).
---

# Block Shim

Pausa uma task com motivo obrigatorio. Move status para `Bloqueada` preservando WIP. Para retomar, use `unblock`. Para encerrar definitivo, use `cancel`.

Call the core process script:

```powershell
.\core\bin\ai.ps1 block F-000 --reason "Motivo curto"
```

- `--reason` e obrigatorio (fica em `task.blocks[]`).
- Bloqueia se a task ja esta em estado terminal ou ja em `Bloqueada`.

Depois continue usando `ai-process`.
