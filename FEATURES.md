# Features e Issues

---

## [F-002] Enxugar README seguindo Standard Readme

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** README tinha ~120 linhas misturando intro, layout, paridade entre agentes, copy table de instalacao e roadmap. Padrao Standard Readme manda responder em ordem com cortes (o que e, por que, instalar, usar, links para o resto). Mover detalhe para docs/INSTALL.md e docs/ROADMAP.md; manter README como porta de entrada.

### Arquivos modificados/criados

- `FEATURES.md`
- `README.md`
- `docs/INSTALL.md`
- `docs/ROADMAP.md`

### O que foi feito

- Demanda criada via ai-process.
- README reduzido de ~120 para 53 linhas na ordem Standard Readme (o que e -> por que -> instalar -> usar -> links). docs/INSTALL.md absorveu a copy table e bootstrap; docs/ROADMAP.md absorveu as 4 entradas de roadmap.
- Commit feito manualmente apos finish para nao misturar com arquivos do F-001 ainda nao commitados (skills/agents/* e skills/claude/* deletados, FEATURES.md de F-001 ja estava em e053a84).

### Validacao feita

- Inspecao visual do README e verificacao de que todos os links da secao Documentacao apontam para arquivos existentes (ls docs/).

### Validacao pendente

- Nenhuma.

## [I-002] Diátaxis para docs/: confirmar escopo vs README/CHANGELOG e implementar

- **Status:** Em desenvolvimento
- **Origem:** AI process (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Diátaxis para docs/: confirmar escopo vs README/CHANGELOG e implementar

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via ai-process.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


## [F-001] Reestruturar skills/ com generated/ e deprecar .claude/commands

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Mirror-the-destination: skills/generated/.agents/skills/ (Codex+Antigravity) e skills/generated/.claude/skills/ (Claude). Remove arvore .claude/commands/ (legado segundo docs Anthropic). Atualiza manifest, render-skills.py, README.

### Arquivos modificados/criados

- `FEATURES.md`
- `skills/manifest.yaml`
- `scripts/render-skills.py`
- `README.md`
- `docs/AI_PROCESS.md`
- `CHANGELOG.md`
- `skills/generated/`

### O que foi feito

- Demanda criada via ai-process.
- Manifest: claude_command convertido em claude_skill em todos os verbos; validate (deprecated) removido. Render: alvos passam a sair em skills/generated/.agents/skills/ e skills/generated/.claude/skills/, target claude_command removido. Apagadas as arvores skills/agents/ e skills/claude/. README/AI_PROCESS/CHANGELOG atualizados refletindo a nova estrutura mirror-the-destination.
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/render-skills.py (16/16 alvos gerados), python scripts/render-skills.py --check (OK)

### Validacao pendente

- Nenhuma.

## [I-001] Paridade de skills/comandos entre Claude, Codex e Antigravity - usar fonte unica

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Paridade de skills/comandos entre Claude, Codex e Antigravity - usar fonte unica

### Arquivos modificados/criados

- `FEATURES.md`
- `skills/manifest.yaml`
- `scripts/render-skills.py`
- `scripts/ai.py`
- `README.md`
- `skills/agents/ai-process/SKILL.md`
- `skills/agents/promote/SKILL.md`

### O que foi feito

- Demanda criada via ai-process.
- Manifest YAML unico em skills/manifest.yaml como fonte de verdade dos verbos por agente.
- Renderer scripts/render-skills.py gera .agents/skills, .claude/commands e .claude/skills a partir do manifest.
- Subcomando 'ai render' (com --check e --verb) wrappa o renderer mantendo UX via ai.ps1.
- README documenta paridade: Codex+Antigravity compartilham .agents/skills; Claude usa commands+skills; edicao passa pelo manifest.
- ai-process SKILL agora cita Antigravity explicitamente e referencia o workflow do manifest.

### Validacao feita

- ai render --check -> OK: 17 alvo(s) em sincronia com o manifest.
- ai render (idempotente): segunda execucao nao grava nada.

### Validacao pendente

- Nenhuma.

