# Roadmap

Versao atual: ver [`VERSION`](../VERSION) e [`CHANGELOG.md`](../CHANGELOG.md).

## Entregue

- **v0.1** — Extracao inicial do projeto `gerador-cortes`; skill+script+JSON funcionando.
- **F-009** — Adocao do layout oficial de plugin Claude Code (`dist/.claude-plugin/`, namespace `ai`).
- **F-011** — Reorganizacao do repo-mae em `core/` (fontes) + `dist/` (build).
- **F-012** — Renderer + `dist/bin/` standalone para o plugin.
- **F-013** — Instalador oficial `install.ps1`/`install.sh` (substituiu a versao planejada para v0.2). Idempotente, com `--dry-run`, `--force` e `--skip-init`.
- **Onda ADR-0011 (F-030 -> D-045) + B-017** — Modelo de demanda redesenhado em 5 fases: ID neutro `D-NNN`, `kind` plural (`feature`/`bug`/`chore`), backlog como status em `tasks.json`, status `Planejada` + verbos `plan`/`start`, troca limpa de `issue` por `bug`, marcadores visuais (emojis) por kind. Decisao em [`docs/adr/0011-modelo-de-demanda-tipo-x-status.md`](adr/0011-modelo-de-demanda-tipo-x-status.md).

## A caminho

- **B-009 (proxima grande)** — Publicar marketplace remoto em `github.com/paulosmarcos/guia-fluxo` para `/plugin marketplace add paulosmarcos/guia-fluxo` direto, sem clonar o repo.
- **`ai --version`** — leitura de `VERSION` + campo `packVersion` em `process.json` para rastrear qual versao do pack cada projeto consome.
- **Testes de smoke do CLI** + documento de migracao entre versoes do pack (rumo a v1.0).

## Backlog conceitual

Itens vivos em [`.guia/backlog.json`](../.guia/backlog.json). Dependencias arquiteturais maiores estao registradas como ADRs em [`docs/adr/`](adr/) (ex.: ADR-0011 sobre modelo de demanda).
