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

Lista completa de arquivos a copiar: [`docs/INSTALL.md`](docs/INSTALL.md).

## Uso

```powershell
.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\scripts\ai.ps1 status
.\scripts\ai.ps1 ready F-016 --file scripts/ai.py --summary "Implementacao pronta"
.\scripts\ai.ps1 finish F-016 --lock --lock-id ai-process-pack
```

Cada comando atualiza `.ai/*.json`, `FEATURES.md` e imprime um titulo sugerido
(`NOME DO CHAT: F-016 - #DEV - Titulo`) que o agente repete e tenta aplicar via
API/comando da ferramenta quando disponivel.

## Documentacao

- [`docs/AI_PROCESS.md`](docs/AI_PROCESS.md) — desenho do processo, fluxo completo, comandos e paridade entre agentes.
- [`docs/INSTALL.md`](docs/INSTALL.md) — lista de arquivos a copiar e bootstrap em outro projeto.
- [`docs/PROTOCOL.md`](docs/PROTOCOL.md) — protocolo de lock de funcionalidades.
- [`docs/HOOKS.md`](docs/HOOKS.md) — uso dos hooks git.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — proximas versoes.
- [`CHANGELOG.md`](CHANGELOG.md) — historico de mudancas.

## Licenca

A definir.
