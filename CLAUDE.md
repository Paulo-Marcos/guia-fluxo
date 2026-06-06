# CLAUDE.md

Pointer fino para Claude Code. **O briefing canonico esta em [`AGENTS.md`](AGENTS.md)** - leia ele primeiro. Este arquivo so cobre o que e especifico do Claude Code (plugin, shortcuts, API de renomeacao).

## Plataforma do usuario

Windows, PowerShell. Use sintaxe PowerShell nos comandos: `$null`, `$env:VAR`, backtick para continuacao, `if ($?)` em vez de `&&`. Bash continua disponivel via tool para scripts POSIX, mas docs e exemplos usam PowerShell. CLI principal: `.\core\bin\ai.ps1 <sub>`.

## Skills do plugin (namespace `ai`)

Este repo **e um plugin Claude Code oficial**: `dist/.claude-plugin/plugin.json` expoe as skills sob namespace `ai`. Quando o usuario digitar uma das shims abaixo, dispare a skill correspondente em `dist/skills/<verbo>/SKILL.md`. **Nao reimplemente a logica inline** - cada shim ja chama `core/src/ai.py` corretamente via `core/bin/ai.ps1`.

| Atalho | Skill | Quando usar |
| --- | --- | --- |
| `/ai:feature` | `feature` | Nova capacidade pedida explicitamente. |
| `/ai:issue` | `issue` | Bug, regressao ou divida tecnica curta. |
| `/ai:backlog` | `backlog` | Ideia futura, sem prazo / sem decisao tomada. |
| `/ai:promote` | `promote` | Converter item de backlog em feature/issue ja avaliado. |
| `/ai:ready` | `ready` | Implementacao pronta para validacao humana. **A IA dispara, nao o humano.** |
| `/ai:finish` | `finish` | Validacao confirmada, fechar e (opcional) travar. |
| `/ai:status` | `status` | Inspecao da task atual. |
| `/ai:cancel` | `cancel` | Encerrar task como Cancelada (terminal). Exige `--reason`. |
| `/ai:block` | `block` | Pausar task preservando WIP. Exige `--reason`. |
| `/ai:unblock` | `unblock` | Retomar task pausada. |

A skill mae `ai-process` em `dist/skills/ai-process/SKILL.md` carrega contexto compartilhado. Descriptions foram diferenciadas em F-003 para evitar trigger collision - confie no roteador e nao force uma skill diferente da que o usuario invocou.

### Descoberta automatica

O repo tem `dist/.claude-plugin/marketplace.json` (catalogo) + `.claude/settings.json` com `extraKnownMarketplaces` apontando para `./dist`. Ao abrir o repo em Claude Code (primeira vez), confirme o prompt de trust + instalacao do marketplace local. Depois disso, `/ai:feature` e cia ficam disponiveis em todas as sessoes futuras sem flag. Alternativas pra primeira vez: `claude --plugin-dir ./dist` ou `/plugin marketplace add ./dist` + `/plugin install ai@ai-process-pack` manualmente. Decisao em [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md).

## Especificidades Claude Code

- **Edicao de arquivo:** use as tools `Edit`/`Write` (nao bash heredoc). A regra geral de "nao editar gerados" de AGENTS.md se aplica integralmente.
- **NOME DO CHAT:** sempre que o CLI imprimir essa linha, repita ao usuario. Se a sessao expoe `/rename`, aplique tambem com o titulo sugerido - a maioria das versoes do Claude Code suporta.
- **Sandbox de hooks:** o sistema ja proibe pular hooks (`--no-verify`, `--no-gpg-sign`). Se o hook bloquear, investigue.

## O resto

Regras nao-negociaveis, fluxo padrao por turno, comandos uteis, convencoes de commit, verificacao antes de entregar, lista de "o que nao fazer": tudo em [`AGENTS.md`](AGENTS.md). Volta la se tiver duvida - este arquivo nao duplica nada.
