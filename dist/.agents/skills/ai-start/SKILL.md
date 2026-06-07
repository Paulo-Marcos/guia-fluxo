---
name: ai-start
description: START — comeca trabalho em uma task Planejada ou diretamente Backlog (status -> Em desenvolvimento). Triggered by /start or "$start" / "comecar tarefa / iniciar trabalho / bora codar". Diferente de $promote: assume triagem feita (kind ja decidido). Falha se task ja Em desenvolvimento ou terminal. Do NOT use for: criar nova task do zero (use $feature ou $issue), triar backlog item (use $promote), ou retomar pausa (use $unblock).
---

# Start Shim

Inicia trabalho em uma task `Planejada` ou `Backlog` (status -> `Em desenvolvimento`). Pressupoe triagem feita; se precisa decidir kind, use `$promote`.

Call the core process script:

```powershell
.\core\bin\ai.ps1 start D-NNN [--note "..."]
```

Falha se a task ja esta `Em desenvolvimento`, terminal ou `Bloqueada` (use `$unblock`).

Depois continue usando `ai-process`.
