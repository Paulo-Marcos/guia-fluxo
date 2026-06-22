# CLAUDE.md

Pointer fino para Claude Code. **O briefing canonico esta em [`AGENTS.md`](AGENTS.md)** - leia ele primeiro. Este arquivo so cobre o que e especifico do Claude Code (plugin, shortcuts, API de renomeacao).

## Plataforma do usuario

Windows, PowerShell. Use sintaxe PowerShell nos comandos: `$null`, `$env:VAR`, backtick para continuacao, `if ($?)` em vez de `&&`. Bash continua disponivel via tool para scripts POSIX, mas docs e exemplos usam PowerShell. CLI principal: `.\core\bin\guia.ps1 <sub>`.

## Skills do plugin (namespace `guia`)

Este repo **e um plugin Claude Code oficial**: `plugins/guia/.claude-plugin/plugin.json` (name `guia`) expoe cada verbo como um **command** de plugin em `plugins/guia/commands/<verbo>.md`, namespaced como `/guia:<verbo>`. Quando o usuario digitar uma das shims abaixo, dispare o command correspondente. **Nao reimplemente a logica inline** - cada command ja chama o motor corretamente via `${CLAUDE_PLUGIN_ROOT}/bin/guia.py` (sem clone). (Plugin *skills* surgiriam bare, ex.: `/init` colidindo com o nativo - por isso usamos `commands/`.)

| Atalho | Skill | Emoji | Quando usar |
| --- | --- | --- | --- |
| `/guia:feature` | `feature` | ✨ | Nova capacidade pedida explicitamente. |
| `/guia:bug` | `bug` | 🐛 | Defeito, regressao, comportamento incorreto. |
| `/guia:chore` | `chore` | 🧹 | Manutencao sem mudanca de comportamento (refactor pequeno, deps, build/lint). |
| `/guia:backlog` | `backlog` | — | Ideia futura. `add` parqueia; `list` une fontes; `migrate` move legacy `B-NNN`. |
| `/guia:promote` | `promote` | — | Converter item de backlog em demanda triada (avalia kind + plano antes de comecar). |
| `/guia:plan` | `plan` | — | Marcar task como `Planejada` (triada mas nao iniciada). Aceita transicao de Backlog/Em desenvolvimento. |
| `/guia:start` | `start` | — | Comecar trabalho em task Planejada/Backlog (status -> Em desenvolvimento). |
| `/guia:ready` | `ready` | — | Implementacao pronta para validacao humana. **A IA dispara, nao o humano.** |
| `/guia:finish` | `finish` | — | Validacao confirmada, fechar e (opcional) travar. |
| `/guia:status` | `status` | — | Inspecao da task atual (read-only). |
| `/guia:cancel` | `cancel` | — | Encerrar task como Cancelada (terminal). Exige `--reason`. |
| `/guia:block` | `block` | — | Pausar task preservando WIP. Exige `--reason`. |
| `/guia:unblock` | `unblock` | — | Retomar task pausada. |
| `/guia:init` | `init` | — | Setup do projeto: semeia `.guia/` + deploya lock config (`.guia/locks/registry.yaml`, `lock-ignore.txt`) + `.githooks/commit-msg` + `hooksPath`. Opcional (auto-init ja cobre `.guia/`); `--no-locks` so semeia estado. |
| `/guia:upgrade` | `upgrade` | — | Migra projeto **existente** do layout antigo (`FEATURES.md` + `features/` na raiz) para o atual (`.guia/DEMANDAS.md` + `.guia/locks/`). Idempotente; `--dry-run` lista o plano sem mutar. |

> **Removido na Fase 4 do ADR-0011 (2026-06-07):** `/guia:issue` deixou de existir; use `/guia:bug`. Tasks antigas com `kind=issue` continuam navegaveis (renderizam como "Bug (legacy)" 🐛). IDs novos sao `D-NNN` neutros (ADR-0011); legacy `F-NNN`/`I-NNN`/`B-NNN` continuam aceitos como entrada.

A referencia `guia-fluxo` em `plugins/guia/commands/guia-fluxo.md` carrega contexto compartilhado. Descriptions foram diferenciadas em F-003 para evitar trigger collision - confie no roteador e nao force uma skill diferente da que o usuario invocou.

### Descoberta automatica

O repo tem `.claude-plugin/marketplace.json` na **raiz** (catalogo, `source: ./plugins/guia`) + `.claude/settings.json` com `extraKnownMarketplaces` apontando para `.` (a raiz). Ao abrir o repo em Claude Code (primeira vez), confirme o prompt de trust + instalacao do marketplace local. Depois disso, `/guia:feature` e cia ficam disponiveis em todas as sessoes futuras sem flag. Alternativas pra primeira vez: `claude --plugin-dir ./plugins/guia` (carrega o plugin direto, sem marketplace) ou `/plugin marketplace add .` + `/plugin install guia@guia-fluxo` manualmente. (D-077 removeu o `marketplace.json` interno duplicado de `plugins/guia/.claude-plugin/`, que usava `source: '../'` desaconselhado; ver `docs/adr/0015-plugin-global-first-guia-init.md`.) Decisao em [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md).

## Especificidades Claude Code

- **Edicao de arquivo:** use as tools `Edit`/`Write` (nao bash heredoc). A regra geral de "nao editar gerados" de AGENTS.md se aplica integralmente.
- **NOME DO CHAT:** sempre que o CLI imprimir essa linha, repita ao usuario. Se a sessao expoe `/rename`, aplique tambem com o titulo sugerido - a maioria das versoes do Claude Code suporta.
- **Sandbox de hooks:** o sistema ja proibe pular hooks (`--no-verify`, `--no-gpg-sign`). Se o hook bloquear, investigue.

## O resto

Regras nao-negociaveis, fluxo padrao por turno, comandos uteis, convencoes de commit, verificacao antes de entregar, lista de "o que nao fazer": tudo em [`AGENTS.md`](AGENTS.md). Volta la se tiver duvida - este arquivo nao duplica nada.
