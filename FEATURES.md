# Features e Issues

---

## [I-003] Arquivos de governanca faltando (LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, AGENTS.md, CLAUDE.md)

- **Status:** Em desenvolvimento
- **Origem:** Revisao externa de governanca (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Projeto serio no GitHub precisa de arquivos de governanca minimos. Hoje faltam: LICENSE (README diz 'a definir' = porta fechada para adocao, advogado nao deixa clonar repo sem licenca; sem licenca explicita, copyright manda 'todos os direitos reservados' por padrao), CONTRIBUTING.md (como rodar testes, padrao de commit, fluxo de PR; sem isso cada PR chega bagunçado e gasta tempo educando), SECURITY.md (canal privado para reportar falha; sem isso GitHub deixa o botao 'Report a vulnerability' apontando para issue publica e expoe vulnerabilidade), CODE_OF_CONDUCT.md (Contributor Covenant; comunidade toxica afasta contribuidor), AGENTS.md e CLAUDE.md na raiz (instrucoes para os agentes Claude Code/Codex/Cursor lerem ao abrir o repo - convencao emergente). Decisao: usar MIT como licenca (mais permissiva, alinha com extracao de gerador-cortes). LICENSE entra ja nesta issue; demais arquivos sao itens desta demanda.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via ai-process.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


## [F-004] Dogfood do proprio pack: ai init + githooks + features/

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Pack ensina .ai/ e FEATURES.md mas o repo nao usa: process.json e backlog.json faltam (ai doctor falha), .githooks/ nao instalado, features/registry.yaml ausente. Sem self-use o repo perde credibilidade e o pack nao recebe feedback de seu primeiro usuario. Instalar bootstrap completo aqui mesmo (modelo A: commitar JSON state, gitignore reports/chat-title).

### Arquivos modificados/criados

- `FEATURES.md`
- `.ai/process.json`
- `.ai/backlog.json`
- `.gitignore`
- `.githooks/commit-msg`
- `features/registry.yaml`
- `features/lock-ignore.txt`
- `.ai/tasks.json`
- `.ai/current-task.json`

### O que foi feito

- Demanda criada via ai-process.
- ai init criou .ai/process.json e .ai/backlog.json (doctor agora passa).
- Templates copiados para raiz: .githooks/commit-msg, features/registry.yaml, features/lock-ignore.txt.
- .gitignore exclui .ai/chat-title.txt e .ai/reports/ (volateis); demais JSONs do .ai/ ficam versionados para cross-clone.
- Pack agora dogfooda a si mesmo: bootstrap completo (ai init + .githooks/ + features/) instalado e versionado. Proximo melhoria entra como F-005/I-003 via ai feature/issue, fechando o ciclo.

### Validacao feita

- python scripts/ai.py doctor -> AI process files OK.
- python scripts/ai.py render --check -> OK: 16 alvo(s) em sincronia.
- python bin/check-lock.py list -> lista a trava 'adicoes-exigem-autorizacao' do template.

### Validacao pendente

- Nenhuma.

## [F-003] Diferenciar descriptions das skills para evitar trigger collision

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** As 7 shims (feature, issue, backlog, ready, finish, status, promote) e a ai-process tem descriptions parecidas. O agente fica confuso sobre qual disparar. Cada description precisa de marcadores unicos no inicio (gatilho explicito, escopo, quando NAO usar) para que o roteador escolha a skill certa sem ambiguidade.

### Arquivos modificados/criados

- `FEATURES.md`
- `skills/manifest.yaml`
- `skills/generated/.claude/skills/ai-process/SKILL.md`
- `skills/generated/.claude/skills/feature/SKILL.md`
- `skills/generated/.claude/skills/issue/SKILL.md`
- `skills/generated/.claude/skills/backlog/SKILL.md`
- `skills/generated/.claude/skills/promote/SKILL.md`
- `skills/generated/.claude/skills/ready/SKILL.md`
- `skills/generated/.claude/skills/finish/SKILL.md`
- `skills/generated/.claude/skills/status/SKILL.md`
- `skills/generated/.agents/skills/ai-process/SKILL.md`
- `skills/generated/.agents/skills/feature/SKILL.md`
- `skills/generated/.agents/skills/issue/SKILL.md`
- `skills/generated/.agents/skills/backlog/SKILL.md`
- `skills/generated/.agents/skills/promote/SKILL.md`
- `skills/generated/.agents/skills/ready/SKILL.md`
- `skills/generated/.agents/skills/finish/SKILL.md`
- `skills/generated/.agents/skills/status/SKILL.md`

### O que foi feito

- Demanda criada via ai-process.
- Reescritas as 8 descriptions (ai-process + 7 shims) com marcadores unicos em CAPS (PRIMARY TRIGGER, REFERENCE/BACKGROUND, READ-ONLY, DEFER-AND-PARK, EVALUATE-AND-CONVERT, HANDOFF, CLOSE) e clausula 'Do NOT use for: ... (use )' para eliminar trigger collision entre as skills do pack.

### Validacao feita

- python scripts/render-skills.py --check => OK, 16 alvos em sincronia com o manifest

### Validacao pendente

- Nenhuma.

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

