# guia-fluxo

Processo portavel para agentes de IA (Codex, Claude Code, Antigravity) transformarem
pedidos soltos em demandas rastreaveis: backlog, status, validacao, finalizacao e lock
de funcionalidades homologadas.

> **Status:** v0.1.0. Extracao inicial do projeto `gerador-cortes`.

## Por que existe

Sem processo, o agente esquece o que esta fazendo entre turnos e nao protege
funcionalidades homologadas contra refactor de brinde. Este pack centraliza skill
(interface conversacional), script (`core/src/guia.py`, fonte de verdade) e arquivos
JSON/YAML (estado e lock), com os mesmos verbos espelhados para os tres agentes
suportados.

## Instalacao

O pack segue o **layout oficial de plugin Claude Code**, com fontes em `core/` e build em `dist/` (`dist/.claude-plugin/plugin.json` + `dist/skills/`). O marketplace local (`dist/.claude-plugin/marketplace.json`) e registrado pelo proprio repo via `.claude/settings.json` (path `./dist`). Tres caminhos:

1. **Dogfood / dev (este repo aberto em Claude Code):** ele prompta pra confirmar o marketplace local e instala o plugin `ai`. Atalhos `/guia:feature`, `/guia:issue`, etc. ficam disponiveis automaticamente. (Fallback se nao aparecer o prompt: `/plugin marketplace add ./dist` + `/plugin install ai@guia-fluxo`, ou `claude --plugin-dir ./dist`.)
2. **Instalador oficial em qualquer projeto consumidor (Claude Code, Codex CLI ou Antigravity):** desde F-013, `install.ps1` (Windows) e `install.sh` (Linux/Mac) copiam `dist/` para `.guia-fluxo/` no projeto consumidor, criam `.agents/skills/` (Codex+Antigravity) e rodam `ai init`. Idempotente, com `--dry-run` e `--force`. Receita: [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md).
3. **Marketplace remoto (B-009, planejado):** quando o repo for publicado em `github.com/paulosmarcos/guia-fluxo`, `/plugin marketplace add paulosmarcos/guia-fluxo` + `/plugin install ai@guia-fluxo` substituira o passo de clonar.

Codex e Antigravity descobrem o pack via `.agents/skills/ai-<verbo>/SKILL.md` (convencao AGENTS.md) — o instalador ja deixa a pasta pronta.

## Uso

```powershell
.\core\bin\guia.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\core\bin\guia.ps1 status
.\core\bin\guia.ps1 ready F-016 --file core/src/guia.py --summary "Implementacao pronta"
.\core\bin\guia.ps1 docs-check                                          # hook opcional: lista docs vivos a atualizar
.\core\bin\guia.ps1 finish F-016 --docs-touched docs/reference/cli.md --lock --lock-id guia-fluxo
```

Cada comando atualiza `.guia/*.json`, `FEATURES.md` e imprime um titulo sugerido
(`NOME DO CHAT: F-016 - #DEV - Titulo`) que o agente repete e tenta aplicar via
API/comando da ferramenta quando disponivel.

## Documentacao

Documentacao organizada via [Diataxis](https://diataxis.fr/) - quatro portas por intencao do leitor.

- [`docs/`](docs/) — indice completo (tutorials, how-to, reference, explanation).
- [`docs/tutorials/primeiro-uso.md`](docs/tutorials/primeiro-uso.md) — do clone ate finalizar a primeira demanda.
- [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md) — desenho do processo: skill, script, JSON, YAML, hooks.
- [`docs/reference/cli.md`](docs/reference/cli.md) — todos os comandos de `core/src/guia.py` / `core/bin/guia.ps1`.
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
