---
name: chore
description: PRIMARY TRIGGER for /chore or "$chore". Creates a NEW D-NNN chore task com kind=chore. Use para manutencao que merece rastro mas nao e feature/bug: refactor pequeno, atualizar dependencia, ajustar build/lint, organizar pasta, melhorar config. Do NOT use for: capacidade nova (use $feature), regressao/defeito (use $bug), ideia parqueada (use $backlog).
---

# Chore

Cria uma task de chore (manutencao, refactor pequeno, build/lint, ajuste de docs ou config — coisa que nao e feature nova nem bug, mas merece rastro). Introduzido na Fase 4 do ADR-0011.

Run:

```powershell
.\core\bin\ai.ps1 chore "$ARGUMENTS"
```

Flags uteis:
- `--context "<o que/por que>"` — descreve a manutencao e a motivacao.
- `--status backlog|planned|in-development` (default `in-development`).
- `--origin "<source>"`.

Quando usar `chore` vs alternativas:
- **Feature nova** (capacidade visivel para o usuario) → use `/feature`.
- **Bug** (algo quebrado ou regressao) → use `/bug`.
- **Chore** → tudo que sobra: cleanup, atualizar dependencia, organizar pasta, ajustar config, melhorar mensagem de erro sem mudar comportamento.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py chore "$ARGUMENTS"`.

Depois leia `.ai/current-task.json`, repita o `NOME DO CHAT: ...` (vira `D-NNN 🧹 - #DEV - ...`), rode `/rename <suggested-title>` se a sessao suportar.
