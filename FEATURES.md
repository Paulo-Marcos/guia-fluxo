# Features e Issues

---

## [F-007] .editorconfig e .gitattributes para padronizar line endings cross-platform

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Sem .gitattributes, Windows commita CRLF e Mac/Linux LF: diff inteiro fantasma a cada PR. Pior: pack tem .githooks/commit-msg (shell sem extensao) - bash recusa executar com CRLF, entao o primeiro Mac que clonar quebra o hook de lock. Roadmap promete Unix em v0.3 - sem isso, regressao garantida. Solucao: (a) .editorconfig (UTF-8, LF default, 4 espacos; YAML/JSON 2; Markdown sem trim; ps1/bat CRLF; hooks LF) que padroniza editores (VS Code, JetBrains, Vim leem nativamente); (b) .gitattributes que forca eol=lf no commit/checkout por default e overrides eol=crlf para *.ps1/*.psm1/*.psd1/*.bat/*.cmd e eol=lf explicito para .githooks/* e templates/.githooks/* (cobre o commit-msg sem extensao). Caveats: arquivos ja tracked com CRLF (FEATURES.md, skills/generated/**/SKILL.md) ficam stale ate rodar git add --renormalize . em commit separado; scripts/render-skills.py grava com newline do SO (write_text sem newline=) - fix de 1 linha que fica como follow-up.

### Arquivos modificados/criados

- `FEATURES.md`
- `.editorconfig`
- `.gitattributes`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Adicionados .editorconfig e .gitattributes na raiz. .editorconfig (UTF-8, LF default, 4 espacos; YAML/JSON/TOML em 2; Markdown sem trim_trailing_whitespace; *.ps1/*.psm1/*.psd1/*.bat/*.cmd em CRLF; .githooks/* e templates/.githooks/* em LF; Makefile com tab) padroniza editores VS Code/JetBrains/Vim. .gitattributes (* text=auto eol=lf como base; overrides eol=crlf para PowerShell e batch; eol=lf explicito para .sh/.bash/Python/YAML/JSON/TOML/INI/MD/TXT e para .githooks/* e templates/.githooks/* que cobrem commit-msg sem extensao; *.png/jpg/jpeg/gif/ico/pdf/zip/gz/tar/woff/woff2 marcados binary) garante normalizacao no commit. Validado via git check-attr: .githooks/commit-msg=lf, scripts/ai.ps1=crlf, scripts/ai.py=lf, templates/.githooks/commit-msg=lf.
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/ai.py doctor => AI process files OK. python scripts/render-skills.py --check => OK: 16 alvo(s) em sincronia com o manifest. git check-attr -a confirma rules aplicadas nos arquivos-chave.

### Validacao pendente

- Nenhuma.

## [F-006] Smoke test do fluxo basico do pack (ai init -> feature -> ready -> finish)

- **Status:** Aguardando validacao
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Sem teste automatizado, toda mudanca em ai.py ou render-skills.py e um pulo no escuro: hoje so se sabe que finish --lock ainda funciona rodando manualmente, o que e caro e ninguem faz sempre. Smoke test (engenharia eletrica: liga o aparelho, se nao soltou fumaca o primeiro check passou) cobre o caminho feliz mais comum num arquivo enxuto (~20 linhas, ~2s) e pega 80% das regressoes. Para o pack: tests/test_smoke.py cria diretorio temporario, roda em sequencia ai init / ai feature 'teste' / ai ready F-001 / ai finish F-001 e valida que .ai/tasks.json terminou com status 'Validada' no fim. Justamente porque o projeto e pequeno a barreira pra adicionar 1 teste e baixissima e ganha-se tranquilidade pra refatorar sem medo. Pendencias: (a) escolher framework (unittest da stdlib evita dependencia nova), (b) integrar no .github/workflows/ que entra via F-005 (rodar nos PRs), (c) documentar como rodar em CONTRIBUTING.md.

### Arquivos modificados/criados

- `FEATURES.md`
- `tests/test_smoke.py`
- `.ai/tasks.json`
- `.ai/current-task.json`

### O que foi feito

- Demanda criada via ai-process.
- tests/test_smoke.py adicionado: ~30 linhas, stdlib unittest (zero deps), roda init/feature/ready/finish num tempdir e valida que tasks.json terminou com status Validada. Smoke test sem framework externo.

### Validacao feita

- python -m unittest tests.test_smoke -v -> OK, 1 teste passou em 1.365s.

### Validacao pendente

- Plugar o teste no workflow CI que entra com F-005 (.github/workflows/).
- Documentar 'como rodar testes' no CONTRIBUTING.md.

## [F-005] Pasta .github/ - templates de issue/PR e workflows (lock-check, render-check)

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** PROTOCOL/explanation/por-que-lock e docs/reference/hooks-git prometem que o CI re-checa travas no PR mesmo se o hook local for pulado (terceira camada). O arquivo .github/workflows/lock-check.yml nao existe: a promessa esta no doc mas a execucao nao. Falta tambem template de issue (bug_report) e PR para padronizar relatos. Adicionar (a) .github/ISSUE_TEMPLATE/bug_report.md, (b) .github/ISSUE_TEMPLATE/config.yml apontando o canal de seguranca, (c) .github/PULL_REQUEST_TEMPLATE.md, (d) .github/workflows/lock-check.yml usando python bin/check-lock.py ci, e (e) .github/workflows/render-check.yml para detectar drift do manifest (python scripts/render-skills.py --check + ai doctor). Lock global obriga marcar [unlock:adicoes-exigem-autorizacao] no commit.

### Arquivos modificados/criados

- `FEATURES.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/lock-check.yml`
- `.github/workflows/render-check.yml`
- `CHANGELOG.md`
- `.ai/tasks.json`
- `.ai/current-task.json`

### O que foi feito

- Demanda criada via ai-process.
- Criada estrutura .github/ com 5 arquivos: bug_report.md (template de issue), config.yml (bloqueia issue em branco), PULL_REQUEST_TEMPLATE.md (checklist de demanda/lock/validacao), lock-check.yml (workflow que re-checa python bin/check-lock.py ci no PR - terceira camada do protocolo de lock prometida em docs/explanation/por-que-lock.md), render-check.yml (rodam ai doctor + render-skills.py --check em mudancas que afetam skills/.ai).
- Sem hardcode de URL absoluta: nao ha git remote configurado ainda; config.yml deixa contact_links vazio e aponta para SECURITY.md (rastreado em I-003).
- Pasta .github/ entregue e validada localmente. Commit feito manualmente apos finish para incluir [unlock:adicoes-exigem-autorizacao] no message (5 arquivos novos sob .github/ disparariam o lock global), e para isolar os arquivos da demanda dos demais nao commitados no working tree (CONTRIBUTING.md, LICENSE, SECURITY.md de I-003, deletes do skills/ legados, etc.).

### Validacao feita

- YAML parseado com pyyaml para .github/workflows/{lock-check,render-check}.yml e .github/ISSUE_TEMPLATE/config.yml -> OK.
- Simulado python bin/check-lock.py ci com features de teste: bloqueia add sem [unlock:...] (exit 1, mensagem com instrucao); passa com [unlock:adicoes-exigem-autorizacao] no msg (exit 0).
- python scripts/ai.py doctor -> AI process files OK; python scripts/render-skills.py --check -> 16 alvos em sincronia.

### Validacao pendente

- Nenhuma.

## [I-003] Arquivos de governanca faltando (LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, AGENTS.md, CLAUDE.md)

- **Status:** Validada
- **Origem:** Revisao externa de governanca (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Projeto serio no GitHub precisa de arquivos de governanca minimos. Hoje faltam: LICENSE (README diz 'a definir' = porta fechada para adocao, advogado nao deixa clonar repo sem licenca; sem licenca explicita, copyright manda 'todos os direitos reservados' por padrao), CONTRIBUTING.md (como rodar testes, padrao de commit, fluxo de PR; sem isso cada PR chega bagunçado e gasta tempo educando), SECURITY.md (canal privado para reportar falha; sem isso GitHub deixa o botao 'Report a vulnerability' apontando para issue publica e expoe vulnerabilidade), CODE_OF_CONDUCT.md (Contributor Covenant; comunidade toxica afasta contribuidor), AGENTS.md e CLAUDE.md na raiz (instrucoes para os agentes Claude Code/Codex/Cursor lerem ao abrir o repo - convencao emergente). Decisao: usar MIT como licenca (mais permissiva, alinha com extracao de gerador-cortes). LICENSE entra ja nesta issue; demais arquivos sao itens desta demanda.

### Arquivos modificados/criados

- `FEATURES.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `.ai/current-task.json`
- `.ai/tasks.json`
- `docs/README.md`
- `docs/explanation/por-que-lock.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`

### O que foi feito

- Demanda criada via ai-process.
- Adicionados os 5 arquivos de governanca + LICENSE MIT (entregue na resposta anterior) + atualizacao do README com secao 'Contribuindo' e troca de 'A definir' por link para MIT.
- LICENSE: MIT padrao, copyright 2026 Paulo Marcos.
- CONTRIBUTING.md: pre-requisitos, setup, fluxo via ai-process (issue/feature -> ready -> finish), edicao de skills via manifest + render, padrao de commit (feature:/issue:/chore: + [unlock:<id>]), PR.
- SECURITY.md: canal privado paulolinhodboa@gmail.com + GitHub Security Advisory, prazos (5 dias uteis para acuse, 10 para avaliacao), escopo (bypass de lock/render, corrupcao de .ai, injecao em CLI).
- CODE_OF_CONDUCT.md: Contributor Covenant v2.1 traduzido, contato paulolinhodboa@gmail.com.
- AGENTS.md: brief generico (Codex/Cursor/Antigravity) - regras nao-negociaveis (script e fonte de verdade, nao editar skills/generated, respeitar lock), fluxo padrao, comandos uteis, anti-padroes.
- CLAUDE.md: brief especifico Claude Code - skills locais, PowerShell, regras + verificacao antes de entregar, anti-padroes.
- Demanda finalizada via ai-process.

### Validacao feita

- .\\scripts\\ai.ps1 doctor => AI process files OK.
- python scripts/render-skills.py --check => OK, 16 alvos em sincronia com o manifest

### Validacao pendente

- Nenhuma.

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

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Diátaxis para docs/: confirmar escopo vs README/CHANGELOG e implementar

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/README.md`
- `docs/tutorials/primeiro-uso.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/configurar-hooks-git.md`
- `docs/how-to/promover-backlog.md`
- `docs/how-to/renomear-chat.md`
- `docs/how-to/travar-arquivo.md`
- `docs/how-to/editar-arquivo-travado.md`
- `docs/how-to/destravar-arquivo.md`
- `docs/how-to/renomear-arquivo-travado.md`
- `docs/how-to/auditar-desbloqueios.md`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `docs/reference/registry-yaml.md`
- `docs/reference/hooks-git.md`
- `docs/reference/chat-rename-suporte.md`
- `docs/reference/troubleshooting.md`
- `docs/explanation/visao-geral.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`
- `docs/explanation/por-que-lock.md`
- `docs/explanation/convencoes-de-lock.md`
- `docs/explanation/por-que-diataxis.md`
- `README.md`
- `CHANGELOG.md`
- `features/registry.yaml`
- `templates/features/registry.yaml`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- docs/ reorganizada via Diataxis: 1 tutorial, 9 how-tos, 6 references, 5 explanations. Removidos AI_PROCESS/PROTOCOL/HOOKS/INSTALL (conteudo migrado sem perda). README, CHANGELOG e comments do registry atualizados.
- Demanda finalizada via ai-process.

### Validacao feita

- ls docs/ confirma estrutura; grep por docs/AI_PROCESS|PROTOCOL|HOOKS|INSTALL retorna so historico imutavel (CHANGELOG, FEATURES.md, .ai/tasks.json) e a explanation por-que-diataxis.md (referencia intencional ao antes)

### Validacao pendente

- Nenhuma.

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

