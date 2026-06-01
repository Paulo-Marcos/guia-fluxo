# Changelog

Todas as mudancas notaveis deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Fixed
- **Skills do pack agora ficam habilitadas no proprio repo-mae (I-004).** `scripts/render-skills.py` passou a escrever em quatro destinos: `skills/generated/.claude/skills/` e `skills/generated/.agents/skills/` (stages de distribuicao para projetos consumidores) **e** `.claude/skills/` e `.agents/skills/` na raiz (ativo runtime do dogfood). Antes, so o stage era emitido - como Claude Code/Codex descobrem skills em `.claude/skills/` / `.agents/skills/` na raiz, os atalhos (`/feature`, `/issue`, etc.) nao funcionavam durante o desenvolvimento do proprio pack. Doc desalinhada em `CLAUDE.md`/`AGENTS.md`/`docs/reference/cli.md` corrigida.

### Added
- **Hook de docs no `/finish` (F-010).** O `ai.py finish` agora consulta `.ai/docs-map.yaml` (opcional), lista docs candidatos a atualizacao e bloqueia o fechamento ate o agente registrar `--docs-touched <path>` ou `--docs-skip "<motivo>"`. Quando o mapa nao existe, vira no-op com aviso. Subcomando standalone `ai.py docs-check [--json]` exposto para consulta. Schema em [`docs/reference/docs-map.md`](docs/reference/docs-map.md), receita em [`docs/how-to/manter-docs-atualizados.md`](docs/how-to/manter-docs-atualizados.md), racional em [`docs/explanation/por-que-docs-hook.md`](docs/explanation/por-que-docs-hook.md), decisao em [`docs/adr/0005-docs-hook-no-finish.md`](docs/adr/0005-docs-hook-no-finish.md).
- Pasta [`.github/`](.github/) com templates e workflows do GitHub:
  - [`.github/ISSUE_TEMPLATE/bug_report.md`](.github/ISSUE_TEMPLATE/bug_report.md) e [`.github/ISSUE_TEMPLATE/config.yml`](.github/ISSUE_TEMPLATE/config.yml) (bloqueia issue em branco).
  - [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) com checklist de demanda, locks e validacoes.
  - [`.github/workflows/lock-check.yml`](.github/workflows/lock-check.yml) - terceira camada do lock: re-checa no PR via `python bin/check-lock.py ci` mesmo se o hook local foi pulado.
  - [`.github/workflows/render-check.yml`](.github/workflows/render-check.yml) - roda `ai doctor` e `render-skills.py --check` em mudancas que afetam skills ou `.ai/`.

### Changed
- `docs/` reorganizada via framework [Diataxis](https://diataxis.fr/): conteudo separado em `tutorials/`, `how-to/`, `reference/` e `explanation/`. Indice em [`docs/README.md`](docs/README.md). README do projeto atualizado para apontar para a nova estrutura.

### Removed
- `docs/AI_PROCESS.md`, `docs/PROTOCOL.md`, `docs/HOOKS.md`, `docs/INSTALL.md` (conteudo migrado para a nova estrutura Diataxis sem perda).

## [0.1.0] - 2026-05-31

### Added
- Extracao inicial do projeto gerador-cortes para um repositorio dedicado.
- Motor CLI em Python: `scripts/ai.py` e wrapper PowerShell `scripts/ai.ps1`.
- Verificador de locks: `bin/check-lock.py`.
- Skills geradas em `skills/generated/` espelhando o destino:
  - `skills/generated/.agents/skills/<verb>/SKILL.md` (Codex + Antigravity).
  - `skills/generated/.claude/skills/<verb>/SKILL.md` (Claude Code, ja com slash command).
- Verbos: ai-process, feature, issue, backlog, promote, ready, finish, status.
- Templates de bootstrap em `templates/`:
  - `features/registry.yaml` com lock global `adicoes-exigem-autorizacao`.
  - `features/lock-ignore.txt`.
  - `.githooks/commit-msg`.
- Documentacao em `docs/`: `AI_PROCESS.md`, `PROTOCOL.md` (protocolo de lock), `HOOKS.md` (hooks git).
