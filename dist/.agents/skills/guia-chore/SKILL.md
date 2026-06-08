---
name: guia-chore
description: PRIMARY TRIGGER for /chore or "$chore". Creates a NEW D-NNN chore task com kind=chore. Use para manutencao que merece rastro mas nao e feature/bug: refactor pequeno, atualizar dependencia, ajustar build/lint, organizar pasta, melhorar config. Do NOT use for: capacidade nova (use $feature), regressao/defeito (use $bug), ideia parqueada (use $backlog).
---

# Chore Shim

Cria uma task de manutencao (refactor pequeno, build/lint, deps, config, docs sem mudanca de comportamento). Introduzido na Fase 4 do ADR-0011.

Call the core process script:

```powershell
.\core\bin\guia.ps1 chore "<title>" --context "<o que + por que>"
```

Aceita `--status backlog|planned|in-development`.

Then continue using `guia-fluxo`.
