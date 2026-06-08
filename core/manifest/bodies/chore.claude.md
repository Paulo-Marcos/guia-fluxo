# Chore

Cria uma task de chore (manutencao, refactor pequeno, build/lint, ajuste de docs ou config — coisa que nao e feature nova nem bug, mas merece rastro). Introduzido na Fase 4 do ADR-0011.

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 chore "$ARGUMENTS"
```

Flags uteis:
- `--context "<o que/por que>"` — descreve a manutencao e a motivacao.
- `--status backlog|planned|in-development` (default `in-development`).
- `--origin "<source>"`.

Quando usar `chore` vs alternativas:
- **Feature nova** (capacidade visivel para o usuario) → use `/feature`.
- **Bug** (algo quebrado ou regressao) → use `/bug`.
- **Chore** → tudo que sobra: cleanup, atualizar dependencia, organizar pasta, ajustar config, melhorar mensagem de erro sem mudar comportamento.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py chore "$ARGUMENTS"`.

{{include: _partials/post_cli.claude.md}}

{{include: _partials/lock_protocol.md}}

Then continue with the maintenance work.
