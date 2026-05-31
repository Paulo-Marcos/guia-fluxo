# Roadmap

Versao atual: ver [`VERSION`](../VERSION) e [`CHANGELOG.md`](../CHANGELOG.md).

- **v0.2** — Instalador (`install/install.ps1`) que copia tudo e roda `ai init`
  numa unica invocacao, com flag `--upgrade` que preserva estado.
- **v0.3** — Suporte Unix (`bin/ai.sh`, `install/install.sh`).
- **v0.4** — `ai --version` lendo de `VERSION`; campo `packVersion` em
  `process.json` para rastrear qual versao do pack cada projeto consome.
- **v1.0** — Cobertura de testes minima (smoke do CLI) e documento de migracao
  entre versoes do pack.
