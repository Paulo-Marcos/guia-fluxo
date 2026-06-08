---
name: guia-plan
description: PLAN — marca task como `Planejada` (triada mas nao iniciada). Triggered by /plan or "$plan" / "planejar tarefa / triagem feita / aguardar para comecar". Aceita transicao de Backlog (item parqueado que ganhou prioridade) ou de Em desenvolvimento (despriorizado mas ja conhecido). Do NOT use for: comecar trabalho agora (use $start ou $promote), guardar ideia sem decidir (use $backlog), ou entregar pra validacao (use $ready).
---

# Plan Shim

Marca task como `Planejada` (triada mas nao iniciada). Aceita transicao de `Backlog` ou `Em desenvolvimento`.

Call the core process script:

```powershell
.\core\bin\guia.ps1 plan D-NNN [--note "..."]
```

Falha em estado terminal ou ja `Planejada`. Use `$start` para sair de `Planejada` para `Em desenvolvimento`.

Depois continue usando `guia-fluxo`.
