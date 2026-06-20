# Partials

Trechos de markdown reutilizaveis incluidos em bodies de skill via
`{{include: _partials/<arquivo>.md}}`. O `render-skills.py` expande os
includes em build-time; o `SKILL.md` final em `plugins/guia/` fica
self-contained (nenhuma indirecao em runtime para o agente).

## Convencoes

- Nome do arquivo termina em `.md` (markdown puro, sem frontmatter).
- Sufixo `.agent.md` para Codex/Antigravity, `.claude.md` para Claude Code,
  ou sem sufixo quando o conteudo serve aos dois targets.
- Partials podem incluir outros partials (recursivo); ciclos sao
  detectados e abortam o render.

## Por que existe

Centraliza protocolos compartilhados (post-CLI flow, lock handling,
title/context synthesis) que antes viviam duplicados em cada body de
verbo + na skill-mae `guia-fluxo`. Editar uma regra agora muda todas as
skills que a consomem.

## Catalogo

Ver decisao em `docs/adr/0012-partial-includes-em-bodies.md` (se
existir) ou no commit que introduziu o sistema.
