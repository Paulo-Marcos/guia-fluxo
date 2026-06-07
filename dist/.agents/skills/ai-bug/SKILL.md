---
name: ai-bug
description: PRIMARY TRIGGER for /bug or "$bug". Creates a NEW D-NNN bug/regression task with kind=bug (substitui o antigo /issue removido na Fase 4 do ADR-0011). Use para defeitos, regressoes e comportamento incorreto. Do NOT use for: nova capacidade (use $feature), manutencao sem mudanca de comportamento (use $chore), ideia parqueada (use $backlog) ou avaliar um B-NNN existente (use $promote).
---

# Bug Shim

Cria uma task de bug. Substitui o antigo `issue` (removido na Fase 4 do ADR-0011).

Call the core process script:

```powershell
.\core\bin\ai.ps1 bug "<title>" --context "<sintoma + impacto>"
```

Aceita tambem `--status backlog|planned|in-development` para criar ja parqueado ou ja triado.

Then continue using `ai-process`.
