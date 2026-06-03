# Changelog

Todas as mudancas notaveis deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Changed
- **Manifest em layout B: index YAML + bodies markdown (F-016).** `core/manifest/manifest.yaml` migrou de arquivo unico de 422 linhas (todos os bodies inline em `body: |`) para **index curto + 16 arquivos markdown puros** em `core/manifest/bodies/<verb>.<target>.md`. Schema `version: 2` declara `body_file:` por target; renderer resolve o path (relativo a `core/manifest/`), valida path traversal e cacheia leituras (shared body trivial entre targets). Saida em `dist/` permanece **byte-identica**. ADR em [`docs/adr/0008-layout-b-manifest.md`](docs/adr/0008-layout-b-manifest.md). Testes em `tests/test_manifest_layout_b.py`.

### Changed
- **Refactor SOLID/Clean Architecture do `core/` (F-015).** `core/src/ai.py` decomposto de **965 -> ~205 linhas** em 17 modulos sob `core/src/_*.py` (constantes, infra, dominio, application/CLI) e 1 modulo de lock reutilizavel em `core/lock/lock_api.py`. `check-lock.py` virou CLI fino sobre `lock_api`. `core/build/render-skills.py` ganhou hardening (`dataclass Output`, `--check-orphans`, abort em marker ausente, validacao YAML de templates, abort em description vazia). Wrappers: `core/bin/ai.ps1` com `Resolve-Python` em 6 camadas + validacao 3.10+ + diagnostico rico; novo `core/bin/ai` POSIX simetrico. Bodies do manifest ajustados (--context em feature/issue, worktree branch `codex/<slug>` em promote, rodape `ai-process` em promote+finish). Renderer empacota agora **todo o pacote** (`core/src/*.py` + `core/lock/lock_api.py`) em `dist/bin/` flat, mantendo plugin standalone. Total de alvos sob `--check` foi de 22 para 40. Suite de testes expandida de 4 para **63 testes** em `tests/`. ADR em [`docs/adr/0007-arquitetura-modular-core-src.md`](docs/adr/0007-arquitetura-modular-core-src.md). Relatorio em [`docs/auditorias/F-014-validacao.md`](docs/auditorias/F-014-validacao.md).

### Fixed
- **Bugs do CLI e check-lock identificados na auditoria F-014 (I-005).** Corrigidos dentro do refactor F-015: `cleanup_task_worktree` chamado uma vez so em `finish`; `cmd_promote` constroi task+worktree antes de mutar backlog (anti-perda de item); `commit_task` normaliza paths Windows; `find_task_or_current` sugere IDs recentes; `--no-commit` agora preserva worktree; mensagem clara quando `git` nao esta no PATH; `attach_worktree` pre-checa existencia de branch; `validate` imprime warning de deprecacao; `check-lock audit` pre-checa `.git/`; `check-lock lock` ganhou `--allow-missing`; `[unlock:...]` agora exige `motivo:` no mesmo commit; `add_lock` recusa path traversal; `_load_lock_ignore` agora usa `lru_cache`. Wildcard `*` em locks agora respeita `lock-ignore.txt` (antes bypassava). Testes anti-regressao em `tests/test_lock_api.py` e `tests/test_cli_promote_order.py`.

### Added
- **Instalador oficial `install.ps1` / `install.sh` (F-013, B-008 passos 3+4).** Scripts na raiz do repo-mae que copiam `dist/` para o layout final no projeto consumidor: `.ai-process/.claude-plugin/`, `.ai-process/skills/`, `.ai-process/bin/` (plugin Claude num so lugar); `.agents/skills/ai-*/` na raiz (cross-tool Codex+Antigravity); e templates opcionais (`.githooks/commit-msg`, `features/registry.yaml`, `features/lock-ignore.txt`) que **preservam customizacao** do consumidor (use `-Force` / `--force` pra sobrescrever). Roda `ai init` ao final pra semear `.ai/`. Flags: `-Target`/`--target`, `-DryRun`/`--dry-run`, `-Force`/`--force`, `-SkipInit`/`--skip-init`. Idempotente: re-rodar substitui o plugin pelo build atual mas preserva estado (`.ai/`) e customizacoes. Renderer ganhou `dist/templates/` espelhando `core/templates/` (3 alvos: hook git + 2 yaml/txt de lock). Total de alvos do `--check` foi para 22. Novo `tests/test_install.py` simula install em tempdir e valida layout + frontmatter + shim POSIX + doctor do motor standalone.
- Documento [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md) reescrito com TL;DR via instalador, layout final, tabela de flags, upgrade flow, desinstalar, mapa por agente, e fallback copia-manual.

### Changed
- **Renderer agora empacota motor standalone em `dist/bin/` (F-012, B-008 passos 1+2).** `core/build/render-skills.py` ganhou dois comportamentos novos: (1) skills cross-tool em `dist/.agents/skills/` recebem prefixo `ai-` no nome do diretorio e no frontmatter `name:` (ex.: `ai-feature`, `ai-issue`) para evitar colisao com comandos nativos do Codex/Antigravity; `ai-process` fica intacto (sem duplo prefixo). (2) Render passa a copiar `core/src/ai.py` -> `dist/bin/ai.py` (motor) e `core/bin/ai.ps1` -> `dist/bin/ai.ps1` (com path adaptado para layout flat: `..\\src\\ai.py` reescrito para `ai.py`), alem de gerar shim POSIX `dist/bin/ai`. Output do Claude (`dist/skills/<verb>/`) inalterado. Total passou de 16 para 19 alvos sob `--check`. Pavimenta o passo 3 de B-008 (install.ps1/install.sh) e B-009 (marketplace remoto).

- **Renderer escreve com `newline="\n"` explicito (F-007 follow-up).** Antes, `path.write_text(content)` sem o parametro `newline=` deixava Python traduzir `\n` para `\r\n` no Windows. Problema agudo para `dist/bin/ai` (shim bash): commitado com CRLF, `bash` no Linux/Mac falhava com `bash\r: not found`. Fix combina com a normalizacao de `.gitattributes` (eol=lf default; `*.ps1 eol=crlf` re-aplicado no checkout).

- **Repo-mae reorganizado em `core/` + `dist/` (F-011, B-007).** Fontes do pack ficam em `core/` (subpastas `src/` para `ai.py`, `build/` para `render-skills.py`, `manifest/` para `manifest.yaml`, `lock/` para `check-lock.py`, `hooks/` para `commit-msg`, `templates/` para snippets de install) e o buildado (output do render + plugin manifest) fica em `dist/.claude-plugin/` + `dist/skills/` + `dist/.agents/skills/`. Separa "fabrica" de "produto", prepara B-008 (layout consumidor com `.ai-process/`) e B-009 (marketplace remoto). Self-dogfood do repo-mae aponta o marketplace local pra `./dist` via `.claude/settings.json`; `git config core.hooksPath` migrou de `.githooks` para `core/hooks`. Wrapper `.\core\bin\ai.ps1` mantido como entry point e roteia internamente pra `core/src/ai.py`. Docs atualizadas com os novos paths.

- **Layout oficial de plugin Claude Code (F-009).** O repo-mae virou um plugin Claude Code oficial: `.claude-plugin/plugin.json` na raiz (name=`ai`), skills geradas em `skills/<verbo>/SKILL.md` (output do plugin) e `.agents/skills/<verbo>/SKILL.md` (cross-tool Codex+Antigravity via convencao AGENTS.md). Source do manifest movido de `skills/manifest.yaml` para `plugin-src/manifest.yaml` (skills/ na raiz e agora exclusivamente output). Atalhos no Claude saem namespaced: `/ai:feature`, `/ai:issue`, `/ai:backlog`, `/ai:promote`, `/ai:ready`, `/ai:finish`, `/ai:status`. Codex e Antigravity continuam com `/feature`, `$feature`, etc. via `.agents/skills/`. Razao e tradeoffs em [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md).

### Added
- **Marketplace local autoregistrado (F-009).** `.claude-plugin/marketplace.json` (name=`ai-process-pack`) cataloga o plugin `ai` apontando pra raiz do proprio repo (`source: "./"`). `.claude/settings.json` declara `extraKnownMarketplaces` + `enabledPlugins` apontando pro marketplace local via `source: { source: "directory", path: "." }`, de modo que ao abrir o repo em Claude Code o usuario recebe prompt de instalacao e atalhos `/ai:*` ficam disponiveis nas sessoes futuras sem precisar de `--plugin-dir` ou `/plugin marketplace add` manual. Absorve a demanda que era rastreada como B-001 no backlog.

### Removed
- `skills/generated/.claude/skills/` e `skills/generated/.agents/skills/` (stages de distribuicao) e `.claude/skills/` na raiz - substituidos pelo layout oficial em `skills/` + `.agents/skills/`. `render-skills.py` reduziu de 4 destinos para 2.

### Fixed
- **Skills do pack agora ficam habilitadas no proprio repo-mae (I-004).** `scripts/render-skills.py` passou a escrever em quatro destinos: `skills/generated/.claude/skills/` e `skills/generated/.agents/skills/` (stages de distribuicao para projetos consumidores) **e** `.claude/skills/` e `.agents/skills/` na raiz (ativo runtime do dogfood). Antes, so o stage era emitido - como Claude Code/Codex descobrem skills em `.claude/skills/` / `.agents/skills/` na raiz, os atalhos (`/feature`, `/issue`, etc.) nao funcionavam durante o desenvolvimento do proprio pack. Doc desalinhada em `CLAUDE.md`/`AGENTS.md`/`docs/reference/cli.md` corrigida. (Superado por F-009: layout standalone `.claude/skills/` foi substituido pelo plugin oficial em `.claude-plugin/`.)

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
- Motor CLI em Python: `scripts/ai.py` e wrapper PowerShell `core/bin/ai.ps1`.
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
