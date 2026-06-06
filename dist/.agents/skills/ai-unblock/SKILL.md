---
name: ai-unblock
description: RESUME a paused task — move status de `Bloqueada` para `Em desenvolvimento`. Triggered by /unblock or "$unblock" / "retomar tarefa / desbloquear / dependencia resolvida". Inverso de $block. Falha se a task nao estava em `Bloqueada`. Do NOT use for: criar nova task (use $feature ou $issue), promover backlog (use $promote), ou voltar de cancelamento (cancelamento e terminal - abra nova task).
---

# Unblock Shim

Retoma uma task pausada (`Bloqueada` -> `Em desenvolvimento`).

Call the core process script:

```powershell
.\core\bin\ai.ps1 unblock F-000 [--note "O que destravou"]
```

Falha se a task nao estava em `Bloqueada`.

Depois continue usando `ai-process`.
