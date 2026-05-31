# Changelog

Todas as mudancas notaveis deste projeto serao documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

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
