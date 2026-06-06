# Roadmap

Versao atual: ver [`VERSION`](../VERSION) e [`CHANGELOG.md`](../CHANGELOG.md).

## Entregue

- **v0.1** — Extracao inicial do projeto `gerador-cortes`; skill+script+JSON funcionando.
- **F-009** — Adocao do layout oficial de plugin Claude Code (`dist/.claude-plugin/`, namespace `ai`).
- **F-011** — Reorganizacao do repo-mae em `core/` (fontes) + `dist/` (build).
- **F-012** — Renderer + `dist/bin/` standalone para o plugin.
- **F-013** — Instalador oficial `install.ps1`/`install.sh` (substituiu a versao planejada para v0.2). Idempotente, com `--dry-run`, `--force` e `--skip-init`.

## A caminho

- **B-009 (proxima grande)** — Publicar marketplace remoto em `github.com/paulosmarcos/ai-process-pack` para `/plugin marketplace add paulosmarcos/ai-process-pack` direto, sem clonar o repo.
- **`ai --version`** — leitura de `VERSION` + campo `packVersion` em `process.json` para rastrear qual versao do pack cada projeto consome.
- **Testes de smoke do CLI** + documento de migracao entre versoes do pack (rumo a v1.0).

## Backlog conceitual

Itens vivos em [`.ai/backlog.json`](../.ai/backlog.json). Dependencias arquiteturais maiores estao registradas como ADRs em [`docs/adr/`](adr/) (ex.: ADR-0011 sobre modelo de demanda).
