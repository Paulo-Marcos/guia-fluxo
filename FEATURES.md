# Features e Issues

---

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

