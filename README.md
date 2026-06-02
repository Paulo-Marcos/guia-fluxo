# ai-process-pack

Processo portavel para agentes de IA (Codex, Claude Code, Antigravity) transformarem
pedidos soltos em demandas rastreaveis: backlog, status, validacao, finalizacao e lock
de funcionalidades homologadas.

> **Status:** v0.1.0. Extracao inicial do projeto `gerador-cortes`.

## Por que existe

Sem processo, o agente esquece o que esta fazendo entre turnos e nao protege
funcionalidades homologadas contra refactor de brinde. Este pack centraliza skill
(interface conversacional), script (`core/src/ai.py`, fonte de verdade) e arquivos
JSON/YAML (estado e lock), com os mesmos verbos espelhados para os tres agentes
suportados.

## Instalacao

O pack agora segue o **layout oficial de plugin Claude Code**, com fontes em `core/` e build em `dist/` (`dist/.claude-plugin/plugin.json` + `dist/skills/`). O marketplace local (`dist/.claude-plugin/marketplace.json`) e registrado pelo proprio repo via `.claude/settings.json` (path `./dist`). Tres caminhos:

1. **Dogfood / dev:** abra o repo em Claude Code; ele prompta pra confirmar o marketplace local e instala o plugin `ai`. Atalhos `/ai:feature`, `/ai:issue`, etc. ficam disponiveis automaticamente. (Fallback se nao aparecer o prompt: `/plugin marketplace add ./dist` + `/plugin install ai@ai-process-pack`, ou `claude --plugin-dir ./dist`.)
2. **Marketplace publico (futuro):** quando publicado em `claude-plugins-community`, `/plugin marketplace add anthropics/claude-plugins-community` + `/plugin install ai@claude-community` instala direto.
3. **Copia manual (qualquer agente, sem Claude Code):** ainda nao ha instalador automatico para o caso multi-agente. Copie os arquivos do pack para o projeto consumidor e inicialize:

```powershell
.\core\bin\ai.ps1 init --project-name "nome-do-projeto"
git config core.hooksPath core/hooks
```

Codex e Antigravity descobrem o pack via `dist/.agents/skills/<verbo>/SKILL.md` (convencao AGENTS.md) - basta a pasta existir. Lista completa de arquivos a copiar: [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md).

## Uso

```powershell
.\core\bin\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\core\bin\ai.ps1 status
.\core\bin\ai.ps1 ready F-016 --file core/src/ai.py --summary "Implementacao pronta"
.\core\bin\ai.ps1 docs-check                                          # hook opcional: lista docs vivos a atualizar
.\core\bin\ai.ps1 finish F-016 --docs-touched docs/reference/cli.md --lock --lock-id ai-process-pack
```

Cada comando atualiza `.ai/*.json`, `FEATURES.md` e imprime um titulo sugerido
(`NOME DO CHAT: F-016 - #DEV - Titulo`) que o agente repete e tenta aplicar via
API/comando da ferramenta quando disponivel.

## Documentacao

Documentacao organizada via [Diataxis](https://diataxis.fr/) - quatro portas por intencao do leitor.

- [`docs/`](docs/) — indice completo (tutorials, how-to, reference, explanation).
- [`docs/tutorials/primeiro-uso.md`](docs/tutorials/primeiro-uso.md) — do clone ate finalizar a primeira demanda.
- [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md) — desenho do processo: skill, script, JSON, YAML, hooks.
- [`docs/reference/cli.md`](docs/reference/cli.md) — todos os comandos de `core/src/ai.py` / `core/bin/ai.ps1`.
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
