# ai-process-pack

Processo portavel para agentes de IA (Codex, Claude Code, Antigravity) transformarem
pedidos soltos em demandas rastreaveis: backlog, status, validacao, finalizacao e lock
de funcionalidades homologadas.

> **Status:** v0.1.0. Extracao inicial do projeto `gerador-cortes`.

## Por que existe

Sem processo, o agente esquece o que esta fazendo entre turnos e nao protege
funcionalidades homologadas contra refactor de brinde. Este pack centraliza skill
(interface conversacional), script (`scripts/ai.py`, fonte de verdade) e arquivos
JSON/YAML (estado e lock), com os mesmos verbos espelhados para os tres agentes
suportados.

## Instalacao

Ainda nao ha instalador automatico. Copie os arquivos do pack para o projeto consumidor
e inicialize:

```powershell
.\scripts\ai.ps1 init --project-name "nome-do-projeto"
git config core.hooksPath .githooks
```

Lista completa de arquivos a copiar: [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md).

## Uso

```powershell
.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\scripts\ai.ps1 status
.\scripts\ai.ps1 ready F-016 --file scripts/ai.py --summary "Implementacao pronta"
.\scripts\ai.ps1 docs-check                                          # hook opcional: lista docs vivos a atualizar
.\scripts\ai.ps1 finish F-016 --docs-touched docs/reference/cli.md --lock --lock-id ai-process-pack
```

Cada comando atualiza `.ai/*.json`, `FEATURES.md` e imprime um titulo sugerido
(`NOME DO CHAT: F-016 - #DEV - Titulo`) que o agente repete e tenta aplicar via
API/comando da ferramenta quando disponivel.

## Documentacao

Documentacao organizada via [Diataxis](https://diataxis.fr/) - quatro portas por intencao do leitor.

- [`docs/`](docs/) — indice completo (tutorials, how-to, reference, explanation).
- [`docs/tutorials/primeiro-uso.md`](docs/tutorials/primeiro-uso.md) — do clone ate finalizar a primeira demanda.
- [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md) — desenho do processo: skill, script, JSON, YAML, hooks.
- [`docs/reference/cli.md`](docs/reference/cli.md) — todos os comandos de `ai.py` / `ai.ps1`.
- [`docs/how-to/`](docs/how-to/) — receitas: travar arquivo, promover backlog, renomear chat, etc.
- [`docs/adr/`](docs/adr/) — Architecture Decision Records (decisoes arquiteturais e o porque).
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — proximas versoes.
- [`CHANGELOG.md`](CHANGELOG.md) — historico de mudancas.

## Contribuindo

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — pre-requisitos, fluxo de demanda, padrao de commit, PR.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — Contributor Covenant v2.1.
- [`SECURITY.md`](SECURITY.md) — como reportar vulnerabilidade em canal privado.
- [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) — briefing para agentes que abrirem o repo.

## Licenca

[MIT](LICENSE). Copyright (c) 2026 Paulo Marcos.
