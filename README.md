# guia-fluxo

[![tests](https://github.com/Paulo-Marcos/guia-fluxo/actions/workflows/tests.yml/badge.svg)](https://github.com/Paulo-Marcos/guia-fluxo/actions/workflows/tests.yml) [![render-check](https://github.com/Paulo-Marcos/guia-fluxo/actions/workflows/render-check.yml/badge.svg)](https://github.com/Paulo-Marcos/guia-fluxo/actions/workflows/render-check.yml) [![release](https://img.shields.io/github/v/release/Paulo-Marcos/guia-fluxo)](https://github.com/Paulo-Marcos/guia-fluxo/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Transforme pedidos soltos a um agente de IA em **demandas rastreáveis** — e proteja o código já homologado contra "refactor de brinde".

`guia-fluxo` é um processo portátil para agentes de IA (Claude Code, Codex, Antigravity). Ele dá ao agente memória de processo entre turnos e um trilho previsível: todo pedido vira uma demanda com ID, status e histórico, e nada de produção é reescrito sem autorização.

> **Status:** v0.4.0 — em uso real. O próprio repositório roda com o processo (dogfood).

## O problema que resolve

Sem processo, um agente de IA:

- **esquece o que estava fazendo** entre um turno e outro;
- **"melhora" código que você não pediu** e quebra o que já funcionava;
- não deixa rastro de *o que* foi feito, *por quê* e *se foi validado*.

guia-fluxo resolve isso com três ideias simples: **demanda** (todo trabalho tem um ID rastreável), **validação humana** (a IA entrega, você aprova) e **lock** (arquivos homologados só mudam com autorização explícita).

## Como funciona

O ciclo de uma demanda, do pedido ao fechamento:

1. **Abre** — você pede algo; o agente cria a demanda: `/feature` (capacidade nova), `/bug` (defeito) ou `/chore` (manutenção). Ela ganha um ID neutro `D-NNN`.
2. **Implementa** — o agente trabalha normalmente. Cada comando imprime a demanda corrente (`NOME DA DEMANDA: D-042 ✨ - #DEV - ...`) pra amarrar o trabalho à demanda.
3. **Pronto pra validar** — ao terminar, o agente dispara o `ready`. *Ele* dispara, não você: é o portão que força a revisão humana.
4. **Você valida em uso real** — passar nos testes não basta; você usa, confirma e só então pede o fechamento.
5. **Fecha** — `finish` encerra a demanda e, opcionalmente, **trava** (lock) os arquivos entregues. A partir daí, mexer neles exige `[unlock:...]` na mensagem de commit.

Ideias paralelas vão pro **backlog** sem interromper o fluxo; quando viram prioridade, `promote` as converte em demanda.

## Instalação

### Claude Code — sem clone (recomendado)

O pack é um plugin publicado. Pré-requisito: **Python 3.10+** no PATH. No projeto onde você quer usar:

```
/plugin marketplace add Paulo-Marcos/guia-fluxo
/plugin install guia@guia-fluxo
```

Pronto — os atalhos `/guia:feature`, `/guia:bug`, etc. ficam disponíveis. O motor vai embutido no plugin (`${CLAUDE_PLUGIN_ROOT}/bin/guia.py`), se ancora no projeto onde você está e cria o `.guia/` sozinho no primeiro comando. **Nada de clonar o repo nem rodar `init` à mão** — os únicos arquivos que aparecem no seu projeto são o estado `.guia/`.

Opcional: rode `/guia:init` uma vez para ativar os **locks**. Ele semeia o `.guia/`, instala a config de lock (`.guia/locks/registry.yaml`, `.guia/locks/lock-ignore.txt`) e o hook `commit-msg`, e aponta o `git core.hooksPath` para `.githooks/`. É idempotente e nunca sobrescreve o que já existe; pule (ou passe `--no-locks`) se não quiser locks.

### Codex / Antigravity — cópia manual

Esses agentes leem `.agents/skills/` (convenção AGENTS.md) e precisam do pack na árvore do projeto. Como os instaladores `install.ps1`/`install.sh` foram **descontinuados** (D-082), a rota atual é a cópia manual: copie `plugins/guia/` e `plugins/guia/.agents/skills/` para o consumidor e rode `python .guia-fluxo/bin/guia.py init`. Passo a passo: [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md). A automação dessa rota cross-tool está em aberto (B-004).

## Uso

Os verbos do dia a dia (Windows usa o wrapper; em Linux/macOS troque por `python core/src/guia.py <verbo>`):

```powershell
.\core\bin\guia.ps1 feature "Titulo curto" --context "Motivo e escopo"   # abre a demanda
.\core\bin\guia.ps1 status                                               # o que estou fazendo agora?
.\core\bin\guia.ps1 ready D-001 --file core/src/foo.py --summary "Pronto pra validar"
.\core\bin\guia.ps1 finish D-001                                         # depois que VOCÊ validar
```

Cada comando atualiza o estado (`.guia/*.json`, `.guia/DEMANDAS.md`) e imprime o `NOME DA DEMANDA`, que o agente repete pra amarrar o trabalho à demanda. É info da demanda, não um título de chat — renomear o chat é opcional. Referência completa: [`docs/reference/cli.md`](docs/reference/cli.md).

## Documentação

Organizada via [Diataxis](https://diataxis.fr/) — quatro portas por intenção do leitor:

- [`docs/tutorials/primeiro-uso.md`](docs/tutorials/primeiro-uso.md) — do clone ao primeiro `finish`.
- [`docs/how-to/`](docs/how-to/) — receitas (travar arquivo, promover backlog, renomear chat…).
- [`docs/reference/cli.md`](docs/reference/cli.md) — todos os comandos.
- [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md) — o desenho do processo.
- [`docs/adr/`](docs/adr/) — decisões arquiteturais (e o porquê).
- [`docs/`](docs/) — índice completo · [`CHANGELOG.md`](CHANGELOG.md) · [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Como é construído

A stack importa menos que o que está acima — mas pra quem for contribuir, são três camadas:

- **Skill** — a interface conversacional que o agente dispara (`/feature`, `/ready`, …).
- **Script** — `core/src/guia.py` é a **fonte da verdade**: toda mutação de estado passa por ele (nunca edite `.guia/*.json` à mão).
- **Estado** — JSON/YAML em `.guia/` (demandas e status) e `.guia/locks/registry.yaml` (locks).

As fontes ficam em `core/`; o build (`python core/build/render-skills.py`) gera `plugins/guia/` — o plugin Claude Code (`plugins/guia/.claude-plugin/`) e as skills cross-tool dos demais agentes. Por que assim: [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md) e [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md).

## Contribuindo

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — pré-requisitos, fluxo de demanda, padrão de commit, PR.
- [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) — briefing para agentes que abrirem o repo.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`SECURITY.md`](SECURITY.md).

## Licença

[MIT](LICENSE). Copyright (c) 2026 Paulo Marcos.
