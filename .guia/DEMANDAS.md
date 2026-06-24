# Demandas

---

## [D-089] ✨ Skill orquestradora por tema: aciona um bolo de skills

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Reativa D-066 (Resolvida; ADR-0016 concluiu que registry e desnecessario). Em vez de um registro, uma skill orquestradora unica (ex: revisao-completa) cujo corpo aciona um conjunto de skills sobre o alvo. Cobre o caso de 'acionar skills por tema/evento' sem catalogo.

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-24: Onda de skills descartada (decisao do dono 2026-06-24); D-095 gate de qualidade no finish cobre o espirito da avaliacao.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-088] ✨ Feature guia: avaliar arquitetura (DDD/SOLID) ao criar lock

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Reativa D-062 (Resolvida indevidamente; ADR-0016). DIFERENTE das outras: e do CORE do guia (integrada ao lock), nao do plugin pessoal. Ao travar (lock), dispara uma skill que avalia a funcionalidade sob DDD/Clean/SOLID e verifica se os arquivos isolam mesmo a feature (responsabilidade unica); sugere patterns pra separar e travar so o que pertence a feature. Abordagem detalhada a definir.

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-24: Onda de skills descartada (decisao do dono 2026-06-24); D-095 gate de qualidade no finish cobre o espirito da avaliacao.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-087] ✨ Skill commits-funcionais: agrupar working tree por funcionalidade (plugin proprio)

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Reativa D-063 (Resolvida indevidamente; ADR-0016). Skill que le o working tree nao commitado, agrupa por funcionalidade e estrutura commits funcionais (um por funcao logica). Parte determinista (ler git status/diff) pode usar a CLI. Plugin do usuario.

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-24: Onda de skills descartada (decisao do dono 2026-06-24); D-095 gate de qualidade no finish cobre o espirito da avaliacao.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-086] ✨ Skill avalia-tema: tema/metodologia vs projeto (plugin proprio)

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Reativa D-064 (Resolvida indevidamente; ADR-0016). Skill que avalia um tema/padrao/conceito, relaciona com o projeto, diz se ja atende / nao atende / o que adaptar, e propoe acoes. Plugin do usuario.

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-24: Onda de skills descartada (decisao do dono 2026-06-24); D-095 gate de qualidade no finish cobre o espirito da avaliacao.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-085] ✨ Skill valida-pasta: auditar pasta/feature com nota (plugin proprio)

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Reativa D-065 (que ficou Resolvida 'absorvida por servico'; ADR-0016 recusou a camada). Abordagem: skill consultiva (SKILL.md) que recebe um alvo, levanta o que faz/por que/se faz sentido, da nota 0-10 e lista melhorias/problemas, reusando skills de qualidade existentes. Mora no plugin de skills do usuario, nao no core do guia.

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-24: Onda de skills descartada (decisao do dono 2026-06-24); D-095 gate de qualidade no finish cobre o espirito da avaliacao.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-090] ✨ Arquivamento de demandas antigas em .guia/DEMANDAS.md (keep N + historico + ai-skip)

- **Status:** Validada
- **Origem:** Backlog (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Follow-up do D-055 (rename ja feito): o catalogo cresce indefinidamente (hoje 72 demandas / ~3000 linhas), agente carrega tudo no contexto a cada operacao. Manter so as N ultimas (param em process.json, default 30) em .guia/DEMANDAS.md; mover as mais antigas para .guia/historico/ (arquivo unico ou por mes) com marcador no topo '<!-- guia-fluxo: archive=true ai-skip=true -->' que o agente checa antes de carregar. Toca _features_md (upsert chama arquivamento), _process_config (param). Cuidado: numeracao de ID e segura (tasks.json autoritativo).

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_features_archive.py`
- `core/src/_features_md.py`
- `core/src/_constants.py`
- `core/src/_process_config.py`
- `plugins/guia/bin/_features_archive.py`
- `plugins/guia/bin/_features_md.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_process_config.py`
- `tests/test_features_archive.py`
- `.guia/process.json`
- `CHANGELOG.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `core/src/_cli_creation.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_tasks.py`
- `core/src/_clock.py`
- `core/src/_tasks.py`
- `core/src/guia.py`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_cli_tasks.py`
- `plugins/guia/bin/_clock.py`
- `plugins/guia/bin/_tasks.py`
- `plugins/guia/bin/guia.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-24: Implementando arquivamento de DEMANDAS.md (keep-N).
- Novo modulo _features_archive.archive_old_entries(): mantem so as N demandas mais recentes em .guia/DEMANDAS.md e move as antigas para .guia/historico/DEMANDAS.md com marcador '<!-- guia-fluxo: archive=true ai-skip=true -->' no topo.
- upsert_features_entry chama archive_old_entries() no fim (1 import + 1 linha) - isolado para merge limpo com D-052, que ja entrou em _features_md.py durante a implementacao sem conflito.
- Param archive.keepInDemandas em process.json (default 30 via ARCHIVE_KEEP_DEFAULT); fallback para 30 quando ausente. tasks.json segue fonte autoritativa de IDs - arquivamento do .md nao afeta geracao de ID. Idempotente: dedup por ID no append ao historico.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python -m pytest tests/ -> 214 passed
- python -m pytest tests/test_features_archive.py -> 4 passed (mantem N + arquiva resto com marcador; no-op abaixo do limite; idempotencia; keep=0)
- python core/build/render-skills.py --check -> OK 66 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [D-052] ✨ Record task timestamps and execution stats

- **Status:** Validada
- **Origem:** Backlog (2026-06-08)
- **Tipo:** Feature
- **Contexto:** Today tasks store only createdAt and updatedAt as dates (no time component). Goal: capture richer timing data to support performance/throughput analysis later.

Required signals (minimum):
- startedAt: precise timestamp when status transitions to Em desenvolvimento (covers both /feature|/bug|/chore created at status=in-development AND /start|/promote from Backlog/Planejada).
- finishedAt: precise timestamp when status reaches a terminal state (Finalizada / Cancelada).
- elapsedTotal: finishedAt - startedAt (wall-clock, including pauses).

Stretch (worth considering):
- readyAt: timestamp when agent runs /ready (lets us measure dev time vs validation wait time separately).
- blocks[]: each block already has reason, but extend with blockedAt + unblockedAt timestamps so we can compute elapsedBlocked = sum(unblockedAt - blockedAt). Then activeTime = elapsedTotal - elapsedBlocked.
- per-phase counts: how many times the task was blocked/unblocked, how many ready->finish cycles (if we ever allow ready being re-triggered).

Use cases:
- Average time-to-validation per kind (feature vs bug vs chore).
- Time spent blocked vs actively developed.
- Detect tasks that sit too long in Aguardando validacao (process bottleneck).

Notes for implementation:
- Use ISO-8601 with timezone (avoid the createdAt: '2026-06-08' format - need full datetime).
- Backfill old tasks: leave new fields null for tasks created before the change (do not invent timestamps).
- Probably touches: _clock.py (timestamp source), _tasks.py (new_task + transition helpers), _cli_creation.py + _cli_lifecycle.py (set the new fields), _features_md.py / _reports.py (surface the new data), .guia/process.json (schema bump?), tasks.json schemaVersion bump.
- Add a 'stats' subcommand or extend 'tasks show --json' to expose computed elapsedTotal/activeTime.
- Test coverage: a new test file simulating create -> block -> unblock -> ready -> finish and asserting the elapsed math.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_clock.py`
- `core/src/_stats.py`
- `core/src/_tasks.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_creation.py`
- `core/src/_cli_tasks.py`
- `core/src/_features_md.py`
- `core/src/_constants.py`
- `core/src/guia.py`
- `tests/test_stats_timing.py`
- `plugins/guia/bin/`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `CHANGELOG.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-24.
- Seam now_iso() (ISO-8601 c/ timezone, override GUIA_NOW p/ testes) + parse_iso em _clock.py; today() intacto
- Novo _stats.py: compute_stats/elapsed_blocked_seconds/format_duration (puro, backfill=null)
- new_task seeda startedAt(in-dev)/readyAt/finishedAt; start/promote carimbam startedAt set-if-absent; ready seta readyAt+readyCount; finish/cancel/validate setam finishedAt; block/unblock gravam blockedAt/unblockedAt precisos
- Subcomando 'stats [id] [--json]' (elapsedTotal/activeTime/blocks/ciclos); secao Timing isolada em _features_md (cobre reports); schemaVersion tasks.json -> 2 (TASKS_SCHEMA_VERSION)
- Dry-close (--no-commit): index compartilhado mistura D-052 e D-090 (paralelo); commit por demanda fica com o usuario

### Validacao feita

- python -m pytest tests/ -q -> 221 passed
- python core/src/guia.py doctor -> Guia Fluxo files OK
- python core/build/render-skills.py --check -> 66 alvos em sincronia

### Validacao pendente

- Nenhuma.

### Timing (D-052)

- **Iniciada:** Nenhuma.
- **Ready:** Nenhuma.
- **Terminada:** 2026-06-24T18:00:57-03:00

## [D-098] 🧹 Reverter gate de finish por env (D-080): finish vira user-authorized por regra de comportamento

- **Status:** Validada
- **Origem:** Feedback do dono (sessao 2026-06-24)
- **Tipo:** Chore
- **Contexto:** D-080 implementou gate por env GUIA_HUMAN_FINISH no cmd_finish. O dono rejeitou em uso: mandar variavel e ruim e NAO deve ficar habilitada; nao quer configurar nem passar parametro pro finish. Novo modelo (confirmado): /guia:finish e solicitado pelo USUARIO; o agente so executa quando o usuario autoriza, e NUNCA dispara finish por conta propria. Sem gate tecnico no CLI - sem env/param/flag (o motor nao consegue distinguir agente de humano sem um sinal, entao o controle vira regra de comportamento documentada). Escopo: remover ENV_HUMAN_FINISH/_require_human_finish/MSG_FINISH_HUMAN_ONLY do core+mirror; reverter testes (test_finish_human_gate + env nos runners de finish); atualizar docs (AGENTS/CLAUDE/manifest/bodies-finish/cli.md/CHANGELOG) pro modelo de autorizacao humana por comportamento. Supersede D-080.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_cli_lifecycle.py`
- `core/src/_constants.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/finish.md`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/commands/finish.md`
- `plugins/guia/.agents/skills/guia-finish/SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CHANGELOG.md`
- `docs/reference/cli.md`
- `tests/test_finish_commit.py`
- `tests/test_epic.py`
- `tests/test_depends.py`
- `tests/test_smoke.py`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Removido o gate por env do finish (D-080): apagados _require_human_finish/_env_truthy + ENV_HUMAN_FINISH/MSG_FINISH_HUMAN_ONLY (core+mirror). cmd_finish agora abre direto em find_task_or_current, com comentario explicando que o controle e regra de comportamento.
- finish nao exige env nem flag. Controle = instrucao do agente: so roda quando o usuario solicita /guia:finish ou autoriza; nunca por conta propria. Docs reescritas: AGENTS.md, CLAUDE.md, manifest, bodies/finish.md, docs/reference/cli.md, CHANGELOG.md.
- Testes: removido tests/test_finish_human_gate.py; revertido o env GUIA_HUMAN_FINISH dos runners (test_finish_commit/epic/depends/smoke) e de tests/test_quality_hook.py (limpeza, import os tirado).
- Commit isolado 28dd205 (D-098 separado do D-095 por reconstrucao a partir do HEAD). Gate por env removido; finish vira regra de comportamento.

### Validacao feita

- python -m pytest tests/test_finish_commit.py tests/test_epic.py tests/test_depends.py tests/test_smoke.py tests/test_quality_hook.py -q -> 35 passed
- python core/src/guia.py doctor -> OK; render-skills.py --check -> 64 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [D-095] ✨ finish: gate de qualidade via skills antes de fechar

- **Status:** Validada
- **Origem:** Backlog (2026-06-22)
- **Tipo:** Feature
- **Contexto:** O usuario quer que o 'finish' SEMPRE rode uma validacao de qualidade do que foi feito antes de fechar a demanda, nao so os comandos de teste atuais. Ideia: ao dar finish, o agente levanta as skills disponiveis (do projeto E globais) que avaliam qualidade de codigo e as aciona sobre o que mudou (modifiedFiles), checando: (a) qualidade do codigo; (b) tamanho de funcoes/arquivos; (c) responsabilidade unica (SRP); (d) cobertura/tests; (e) se precisa refatorar para ficar com boa qualidade -- e, se precisar, refatorar antes de fechar. Infra existente para reusar: ja ha um hook 'runValidationByDefault'/run_validation_commands no finish (core/src/_cli_lifecycle.py:474) que roda COMANDOS; esta demanda estende isso para acionar SKILLS consultivas (ex.: clean-code-review, clean-architecture-guardian, tdd, valida-pasta) e agir sobre os achados. Overlaps a resolver no recorte: D-088 (avalia DDD/SOLID ao criar LOCK -- mesmo espirito, momento diferente), D-085 (skill valida-pasta com nota 0-10) e D-080 (gate humano no finish). Decidir se e: passo automatico do finish no core, ou uma skill orquestradora acionada no momento do finish. Compativel com finish-human-only: roda quando o humano dispara o finish.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_quality_hook.py`
- `core/src/_constants.py`
- `core/src/_process_config.py`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/finish.md`
- `tests/test_quality_hook.py`
- `tests/test_finish_commit.py`
- `plugins/guia/bin/_quality_hook.py`
- `plugins/guia/commands/finish.md`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/guia.py`
- `plugins/guia/bin/_process_config.py`
- `plugins/guia/.agents/skills/guia-finish/SKILL.md`
- `CHANGELOG.md`
- `docs/reference/cli.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-24: Iniciando: gancho de validacao de qualidade por skills no finish (Onda 2, liberado pos-D-080).
- D-095: gate de qualidade consultivo no finish. Novo _quality_hook.py (espelha o docs-hook): cmd_finish chama ensure_quality_review_ok DEPOIS do guard humano D-080 e do docs-gate, ANTES de mutar status. Quando arquivos de produto mudaram (exclui .guia/**), recusa o finish ate o agente confirmar --quality-checked (ou listar --quality-skill) ou pular com --quality-skip. Bloco instrutivo lista arquivos, dimensoes (a-e) e skills candidatas (clean-code-review, clean-architecture-guardian, tdd-dotnet, valida-pasta/D-085).
- Design B (hibrido): core sinaliza+exige, skill guia:finish executa as skills (skills sao LLM-driven, Python nao as roda). Contrato documentado no body finish.md + manifest. Config finish.qualityGateByDefault (default True) liga/desliga; registro persistido em task.qualityReview. Nao duplica D-088 (LOCK-time) nem D-085 (valida-pasta) - referencia.
- Gate de qualidade consultivo no finish (D-095). Fechamento via commit manual com [unlock:] por causa dos 3 arquivos novos (_quality_hook + mirror + teste).

### Validacao feita

- python -m pytest tests/ -q  => 212 passed
- python core/build/render-skills.py --check  => OK 64 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [D-080] ✨ Forcar finish como acao exclusivamente humana (gate na ferramenta)

- **Status:** Validada
- **Origem:** Backlog (2026-06-20)
- **Tipo:** Feature
- **Contexto:** Hoje 'finish' e so convencao (AGENTS.md): nada tecnico impede a IA de rodar finish/commit. O dono exige que finish seja sempre humano e que isso esteja PREVISTO NA FERRAMENTA. Avaliar: (a) flag/env exigindo confirmacao humana (ex: GUIA_HUMAN_FINISH=1 ou --i-am-human) que a IA nao deve setar; (b) hook/guard que detecta contexto de agente; (c) no minimo, doc explicita. Relacionado: finish tambem nao injeta [unlock:] para arquivos novos, forcando commit manual - avaliar --unlock no finish junto (cruza com D-054 enriquecer commit).

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_cli_lifecycle.py`
- `core/src/_constants.py`
- `core/src/guia.py`
- `core/manifest/bodies/finish.md`
- `core/manifest/manifest.yaml`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/guia.py`
- `plugins/guia/commands/finish.md`
- `plugins/guia/.agents/skills/guia-finish/SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`
- `tests/test_finish_human_gate.py`
- `tests/test_finish_commit.py`
- `tests/test_epic.py`
- `tests/test_depends.py`
- `tests/test_smoke.py`
- `CHANGELOG.md`
- `docs/reference/cli.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-23.
- Gate tecnico no topo de cmd_finish (_require_human_finish): finish recusa sem sinal humano explicito (--i-am-human ou env GUIA_HUMAN_FINISH=1). Guard isolado no topo, antes de qualquer mutacao, pra minimizar conflito com D-095.
- Flag --i-am-human adicionada ao parser finish; constantes ENV_HUMAN_FINISH e MSG_FINISH_HUMAN_ONLY em _constants.py. Mirror plugins/guia/bin regenerado via render-skills.py.
- Docs: AGENTS.md/CLAUDE.md agora dizem gate tecnico (nao so convencao); manifest + bodies/finish.md instruem a IA a NUNCA rodar finish nem setar o sinal.
- AJUSTE pedido pelo dono: sinal unico e a env GUIA_HUMAN_FINISH=1 (previa autorizacao do dev). Flag --i-am-human REMOVIDA (era demais). Semantica: com a env setada, ate a IA pode finalizar (dono ja autorizou); sem ela, recusa.
- Gate tecnico no topo de cmd_finish (_require_human_finish, sem args): finish recusa SystemExit sem GUIA_HUMAN_FINISH=1. Isolado no topo, antes de mutacao, pra minimizar conflito com D-095.
- Docs (AGENTS.md/CLAUDE.md/manifest/bodies/finish.md): gate tecnico = previa autorizacao via env; a IA nao seta a env por conta propria. Mirror regenerado, --check OK.
- Gate de finish humano implementado e documentado; commit manual com [unlock:] por causa do arquivo de teste novo (injecao de unlock e D-054, fora de escopo).

### Validacao feita

- python -m pytest tests/ -q -> 198 passed
- python core/src/guia.py doctor -> Guia Fluxo files OK
- python core/build/render-skills.py --check -> 63 alvos em sincronia
- python -m pytest tests/ -q -> 201 passed
- python core/src/guia.py doctor -> OK
- render-skills.py --check -> 63 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [D-054] ✨ Enriquecer mensagem de commit com resumo do que foi feito

- **Status:** Aguardando validacao
- **Origem:** Backlog (2026-06-09)
- **Tipo:** Feature
- **Contexto:** Hoje o commit gerado pelo finish tem formato minimo: '{kind}: {title}\n\nTask: {id}'. Nao ha resumo do que mudou, quais validacoes passaram, ou referencia ao contexto. Melhorias possiveis: (1) incluir o campo summary da task no corpo do commit (o que foi feito); (2) incluir validacoes que passaram; (3) listar arquivos modificados de forma legivel (ja esta em modifiedFiles mas nao aparece no commit); (4) permitir que o agente passe --commit-body 'texto adicional' no finish para complementar a mensagem automatica; (5) avaliar se o formato deveria seguir Conventional Commits mais estritamente (scope, breaking change). Cuidado: a mensagem de commit atual e simples de parsear por ferramentas - nao complexificar sem motivo claro.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_commit.py`
- `core/src/guia.py`
- `core/src/_cli_lifecycle.py`
- `plugins/guia/bin/_commit.py`
- `plugins/guia/bin/guia.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `tests/test_commit_message.py`
- `.guia/backlog.json`
- `core/manifest/bodies/ready.md`
- `plugins/guia/commands/ready.md`
- `plugins/guia/.agents/skills/guia-ready/SKILL.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-23: Enriquecer mensagem de commit do finish (summary/validations/modifiedFiles) + formalizar Conventional Commits; absorve B-019.
- Commit do finish agora usa Conventional Commits com id da task como scope: header {kind}({id}): {title} (preserva convencao do repo feature/bug/chore, nao feat/fix).
- Corpo enriquecido em _commit.build_commit_message(): summary (o que foi feito), bloco Validacoes, bloco Arquivos; cada bloco so aparece se tiver conteudo.
- Rodape Task: {id} mantido literal e por ultimo como ancora estavel para parsers existentes.
- Novo --commit-body no finish anexa texto livre antes do rodape Task:.
- B-019 (formalizar Conventional Commits + id da task) absorvido e resolvido por esta demanda.
- Ajuste (pedido do usuario): se existir uma skill de convencao de commits do usuario (nome/descricao com commit + conventional/convention/gitmoji), o agente a usa para gerar o subject e passa via --commit-subject; senao, engine usa o formato padrao.
- Engine: build_commit_message/commit_task ganharam subject_override — substitui SO o header, preservando corpo (summary/validacoes/arquivos) e rodape Task: {id}.
- Fluxo: --commit-subject persistido em ready (task.commitSubject); finish (humano) consome automaticamente; --commit-subject no finish tem precedencia. Guia do agente adicionada em ready.md (deteccao por padrao de nome; se ambiguo, perguntar ao usuario).

### Validacao feita

- python -m pytest tests/test_commit_message.py tests/test_finish_commit.py -q (10 passed)
- python core/build/render-skills.py --check (OK: 63 alvos em sincronia)
- e2e: ready --commit-subject 'feat(D-001): ...' -> finish -> commit usa o subject da convencao, mantendo corpo+Task: footer.
- python -m pytest tests/test_commit_message.py -q (12 passed)
- python core/build/render-skills.py --check (OK: 63 alvos)

### Validacao pendente

- Para o commit DESTA demanda: o repo (git log) usa 'feature: D-NNN desc' SEM gitmoji, mas a skill conventional-commit-gitmoji esta disponivel na sessao. Confirme se quer que eu prepare um subject gitmoji via --commit-subject ou mantenha o default do engine.

## [D-097] 🧹 Consolidar superficie da raiz (D-094): VERSION fonte unica + community-health em .github/ + fix README

- **Status:** Validada
- **Origem:** D-094 follow-up
- **Tipo:** Chore
- **Contexto:** Executa as propostas aprovadas do diagnostico D-094. P1: VERSION vira fonte unica da versao - build (render-skills.py) passa a ler VERSION e preencher plugin.json/marketplace.json (hoje 0.4.0 esta em 3 lugares sem sincronia, VERSION nao e lido por ninguem). P2: mover CONTRIBUTING.md/SECURITY.md/CODE_OF_CONDUCT.md para .github/ e ajustar refs (README, AGENTS, docs-map.yaml, config.yml). Bonus: corrigir README.md:9 v0.1.0->0.4.0. Nao toca core/src interno (ADR-0017) nem paths de descoberta do plugin.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/build/render-skills.py`
- `tests/test_version_sync.py`
- `docs/adr/0019-version-fonte-unica.md`
- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`
- `docs/auditorias/D-094-raiz-core-plugin.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via Guia Fluxo.
- P1 (VERSION fonte unica): render-skills.py le VERSION e propaga o campo version p/ plugin.json + marketplace.json (replace cirurgico, preserva o resto); render --check acusa drift. collect_version_outputs + _sync_version_text + _read_version. ADR-0019 + AGENTS regra 3 + CHANGELOG. Provado ponta-a-ponta (bump 9.9.9 propaga, revert volta 0.4.0).
- P2 DROPADO por decisao do dono: mover community-health p/ .github/ quebraria ~15 links relativos internos; ganho so cosmetico. Mantidos na raiz; registrado no relatorio D-094.
- Fix README.md:9 v0.1.0 -> v0.4.0 (estava em drift).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python core/src/guia.py doctor -> exit 0
- python core/build/render-skills.py --check -> exit 0 (63 alvos)
- python -m pytest tests/ -> 187 passed (inclui test_version_sync.py 6/6)

### Validacao pendente

- Nenhuma.

## [D-096] ✨ B-018: Tornar current task robusto sob chats concorrentes (hoje e arquivo global, nao por-chat)

- **Status:** Validada
- **Origem:** Backlog B-018 (2026-06-23)
- **Tipo:** Feature
- **Contexto:** Backlog B-018: Investigado: .guia/current-task.json e UNICO arquivo global por copia de trabalho, escrito por set_current_task() em toda criacao/transicao. Um chat = uma task e convencao, NAO imposto pelo codigo. Dois chats na MESMA pasta sobrescrevem current-task; comando sem id explicito (find_task_or_current(None)) pode pegar a task errada: origem dos conflitos observados. Worktree por task ja e o workaround (cada worktree tem seu .guia/, pois .guia/ e versionado). Decidir: escopar current-task por sessao/worktree, ou exigir id explicito em ready/finish/status com warning no fallback. Ligado ao ADR de modelo de demanda.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `core/src/_tasks.py`
- `plugins/guia/bin/_tasks.py`
- `tests/test_current_task_fallback.py`

### O que foi feito

- Backlog B-018 promovido via guia-fluxo.
- Avaliacao IA: Op A escolhida (confirmada pelo dev). current-task.json e global por copia de trabalho; find_task_or_current(None) resolve em silencio e pode pegar a task errada sob 2+ chats na mesma pasta. ADR-0011 (Aceita/implementada) ja reclassificou B-018 como refactor ortogonal - dependencia de design caiu. Op B (escopo por sessao) descartada: motor nao tem conceito de sessao (CLI invocado fresco), exigiria injetar session-id por chamada (=Op A por via fragil) e worktree-por-task ja isola .guia/. 
- Op A (B-018): centraliza aviso de concorrencia em find_task_or_current. Quando id e omitido E ha 2+ tasks Em desenvolvimento, emite aviso em stderr dizendo qual id (current) foi escolhido e pede id explicito. Todos os callers (ready/finish/status/deps/meta) herdam; status --all mantido. stderr nao polui o stdout JSON do status.
- Op B (escopo por sessao) descartada: motor nao tem conceito de sessao; worktree-por-task ja isola .guia/. Decisao registrada no assessment do promote e na ADR-0011 (que ja classificava B-018 como refactor ortogonal).
- Fechada apos validacao humana. modifiedFiles podado de 66 para 7 (residuo do emaranhamento com D-093 removido; commit isolado de D-096).

### Validacao feita

- python -m pytest -q (181 passed, inclui test_current_task_fallback.py: 2 ativas+sem id avisa, 1 ativa silencia, id explicito silencia)
- python core/build/render-skills.py --check (61 alvos em sincronia)
- python core/src/guia.py doctor (OK)
- python -m pytest -q (181 passed, inclui test_current_task_fallback.py)

### Validacao pendente

- Nenhuma.

## [D-093] ✨ Rename: parar de imprimir 'NOME DO CHAT'; usar 'NOME DA DEMANDA' (chat pode ter varias demandas)

- **Status:** Validada
- **Origem:** Backlog (2026-06-22)
- **Tipo:** Feature
- **Contexto:** Hoje todo verbo imprime 'NOME DO CHAT: D-NNN <emoji> - #STATUS - <title>' tentando renomear o chat - mas (a) na pratica o chat NAO eh renomeado automatico (so via /rename manual ou mark_chapter) e (b) com a chegada do epico (D-049) um mesmo chat-pai pode conter VARIAS demandas/stories. Mudar para: imprimir 'NOME DA DEMANDA: ...' (info pura da demanda corrente, sem pretender que e o titulo do chat); deixar a renomeacao do chat como acao OPCIONAL do usuario; quando houver API/comando de rename automatico disponivel (futuro Claude/Codex/Antigravity), oferecer um caminho separado. Tocar: _tasks.print_chat_title (renomear a funcao), MSG/format strings, chat-title.txt (manter o arquivo? avaliar se ainda faz sentido), bodies do manifest que mencionam 'NOME DO CHAT', docs/how-to/renomear-chat.md, ADRs 0004 (chat-title sincronizado) que precisa ser revisado/substituido por novo ADR registrando essa mudanca.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_tasks.py`
- `core/src/_constants.py`
- `core/src/_process_config.py`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/_partials/post_cli.claude.md`
- `core/manifest/bodies/_partials/post_cli.agent.md`
- `core/manifest/bodies/_partials/title_context_rules.md`
- `core/manifest/bodies/epic.md`
- `core/manifest/bodies/guia-fluxo.md`
- `docs/adr/0018-nome-da-demanda-chat-diferente-de-demanda.md`
- `docs/adr/0004-chat-title-sincronizado.md`
- `docs/adr/README.md`
- `docs/how-to/renomear-chat.md`
- `docs/reference/chat-rename-suporte.md`
- `docs/reference/files.md`
- `docs/reference/cli.md`
- `docs/explanation/visao-geral.md`
- `docs/tutorials/primeiro-uso.md`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `CHANGELOG.md`
- `.gitignore`
- `tests/test_constants.py`
- `tests/test_body_partials.py`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `plugins/guia/.agents/skills/guia-backlog/SKILL.md`
- `plugins/guia/.agents/skills/guia-block/SKILL.md`
- `plugins/guia/.agents/skills/guia-bug/SKILL.md`
- `plugins/guia/.agents/skills/guia-cancel/SKILL.md`
- `plugins/guia/.agents/skills/guia-chore/SKILL.md`
- `plugins/guia/.agents/skills/guia-epic/SKILL.md`
- `plugins/guia/.agents/skills/guia-feature/SKILL.md`
- `plugins/guia/.agents/skills/guia-finish/SKILL.md`
- `plugins/guia/.agents/skills/guia-fluxo/SKILL.md`
- `plugins/guia/.agents/skills/guia-plan/SKILL.md`
- `plugins/guia/.agents/skills/guia-promote/SKILL.md`
- `plugins/guia/.agents/skills/guia-ready/SKILL.md`
- `plugins/guia/.agents/skills/guia-start/SKILL.md`
- `plugins/guia/.agents/skills/guia-status/SKILL.md`
- `plugins/guia/.agents/skills/guia-unblock/SKILL.md`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_process_config.py`
- `plugins/guia/bin/_tasks.py`
- `plugins/guia/bin/guia.py`
- `plugins/guia/commands/backlog.md`
- `plugins/guia/commands/block.md`
- `plugins/guia/commands/bug.md`
- `plugins/guia/commands/cancel.md`
- `plugins/guia/commands/chore.md`
- `plugins/guia/commands/epic.md`
- `plugins/guia/commands/feature.md`
- `plugins/guia/commands/finish.md`
- `plugins/guia/commands/guia-fluxo.md`
- `plugins/guia/commands/plan.md`
- `plugins/guia/commands/promote.md`
- `plugins/guia/commands/ready.md`
- `plugins/guia/commands/start.md`
- `plugins/guia/commands/status.md`
- `plugins/guia/commands/unblock.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-23.
- Troquei o print 'NOME DO CHAT'/'CHAT_TITLE=' por 'NOME DA DEMANDA'/'DEMAND_TITLE=' (info pura da demanda corrente). Renomes internos: print_chat_title->print_demand_title, chat_title()->demand_title(), chave chatTitle->demandTitle em current-task.json, chatTitleFormat->demandTitleFormat em process.json (com fallback de leitura da chave legada), CHAT_TITLE_FILE/chat-title.txt->DEMAND_TITLE_FILE/demand-title.txt, CHAT_TITLE_FORMAT_DEFAULT->DEMAND_TITLE_FORMAT_DEFAULT.
- Renomeacao do chat virou OPCIONAL: skills/partials (post_cli claude+agent, epic, guia-fluxo) reescritas para tratar mark_chapter/rename/codex_app.set_thread_title como conveniencia, pulada quando o chat tem varias demandas (epico D-049). Manifest regenerado -> 61 alvos em sync.
- Nova ADR-0018 registra a mudanca (chat != demanda) e SUBSTITUI a ADR-0004. Auditei stdout: nenhum parser depende de 'NOME DO CHAT:'/'CHAT_TITLE='.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python -m pytest tests/ -q -> 178 passed
- python core/src/guia.py doctor -> exit 0
- python core/build/render-skills.py --check -> exit 0 (61 alvos)
- python core/src/guia.py status D-093 -> imprime 'NOME DA DEMANDA: ...' + 'DEMAND_TITLE=...'

### Validacao pendente

- Nenhuma.

## [D-094] ✨ Limpeza: separar core do plugin e justificar expostos

- **Status:** Validada
- **Origem:** Backlog (2026-06-22)
- **Tipo:** Feature
- **Contexto:** O usuario quer reorganizar a raiz do projeto separando claramente o que e CORE (motor/codigo interno do guia-fluxo) do que e de fato o PLUGIN gerado/exposto para consumo. Percepcao atual: ha arquivos demais expostos na raiz. Objetivo da tarefa: (1) inventariar cada arquivo/pasta exposto na raiz; (2) justificar a razao de existencia/exposicao de cada um; (3) entender os motivos que levaram cada um a estar onde esta; (4) avaliar onde da pra reduzir a superficie exposta, consolidando o que e core num lugar so e deixando exposto apenas o necessario ao plugin. Criterio de sucesso: um mapa raiz->(core|plugin|infra) com justificativa por item e uma proposta de consolidacao que diminua arquivos expostos sem quebrar descoberta do plugin (marketplace.json, .claude-plugin, etc).

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `docs/auditorias/D-094-raiz-core-plugin.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-23.
- Inventario completo da raiz (21 entradas) classificado em CORE/PLUGIN/ESTADO/INFRA-DOCS com justificativa por item; diagnostico de que CORE (core/) e PLUGIN (plugins/) ja estao consolidados e a raiz e quase toda convencao irredutivel; proposta priorizada (P1 VERSION orfao, P2 mover community-health p/ .github/, P3 nao-fazer) respeitando ADR-0017 e a descoberta do plugin.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- doctor -> exit 0; render-skills --check -> exit 0 (61 alvos em sincronia)

### Validacao pendente

- Nenhuma.

## [D-081] ✨ finish/commit nao lida com delecao de arquivo e nao faz rollback do status ao falhar

- **Status:** Validada
- **Origem:** Backlog (2026-06-20)
- **Tipo:** Feature
- **Contexto:** Bug real (mordeu no finish D-077, 2026-06-20): _commit.py git_commit usa 'git add -- <files>', que falha em arquivo DELETADO ('pathspec did not match any files') -> finish aborta sem commitar. Pior: o status ja foi mudado para Validada ANTES do commit, sem rollback, deixando estado inconsistente (task Validada mas nada commitado). Corrigir: (a) stage de delecoes (git add -A -- <path> ou git rm) em git_commit; (b) tornar a transicao de status atomica com o commit (so marca Validada se o commit suceder) ou reverter no erro. Cruza com a lacuna de finish nao injetar [unlock:] para arquivos novos (ver D-080 e D-054).

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_git_ops.py`
- `core/src/_cli_lifecycle.py`
- `plugins/guia/bin/_git_ops.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `tests/test_finish_commit.py`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-22.
- git_commit usa 'git add -A -- <files>' para stage de delecoes (alem de adds/mods); finish reverte o status pre-commit se commit_task estourar (atomicidade status<->commit). Espelho do plugin regerado.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- pytest tests/ -> 178 passed (inclui test_finish_commit.py: deletion commita + commit que falha nao deixa status Validada); doctor exit 0; render-skills.py --check exit 0 (61 alvos em sincronia).

### Validacao pendente

- Nenhuma.

## [D-092] ✨ Filho 1

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-22)
- **Tipo:** Feature
- **Contexto:** Filho 1

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Cancelada em 2026-06-24: Scratch do teste de epic->story (D-049); sem WIP real.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-049] ✨ Hierarquia epic -> stories com chat-pai orquestrador

- **Status:** Validada
- **Origem:** Backlog (2026-06-08)
- **Tipo:** Feature
- **Contexto:** Suportar demandas grandes quebradas em sub-features rastreaveis. Mudancas: schema ganha parent_id em task (D-NNN pode apontar pra E-NNN ou outro D-NNN); novos verbos /epic 'Titulo' cria E-NNN e /feature 'Titulo' --under E-001 cria filho; /status E-001 mostra arvore agregada; /finish E-001 falha enquanto algum filho nao estiver Finalizada/Cancelada; naming convention 'E-001/D-100 - #DEV - <child title>' e 'E-001 - #DEV - <epic title>'; cada filho pode ter worktree proprio, finish do pai exige todos worktrees-filho cleanados. Coordenacao cross-chat e async via .guia/*.json (sem IPC ao vivo) - usar lock_api.py existente para evitar race em writes simultaneos. Risco: chat-pai nao sabe automaticamente quando filho terminou; precisa de /status manual ou hook post-finish que atualize flag legivel. NAO implementar especulativamente - promover quando aparecer caso real de epico que justifique.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_constants.py`
- `core/src/_tasks.py`
- `core/src/_cli_creation.py`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/epic.md`
- `tests/test_epic.py`
- `docs/reference/cli.md`
- `CLAUDE.md`
- `docs/adr/0017-manter-core-src-flat.md`
- `docs/adr/README.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_tasks.py`
- `plugins/guia/bin/guia.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-22: Onda 3: epic E-NNN com filhos D-NNN; agregacao no status; finish do pai gated por filhos terminais.
- D-049 entregue de ponta a ponta. Schema: novo kind 'epic' + prefixo proprio 'E-NNN' (numeracao independente de D-NNN); campo parentId em task; hierarquia de 2 niveis (sem aninhar epics). Verbo novo 'guia epic'; flag --under E-NNN em feature/bug/chore valida que parent existe e e Epic. cmd_status detecta Epic e imprime arvore agregada (progresso closed/total + lista de filhos + aviso de bloqueio); cmd_finish recusa Epic com filhos abertos. Cancel NAO cascateia (decisao). STATUSES_SATISFY_DEPENDENCY (D-067) e reusada como definicao de 'filho terminal' - mesmo set Validada/Finalizada/Resolvida/Cancelada. Tambem entrega ADR-0017 (Manter core/src flat / D-053 recusada) - avaliacao da proposal-architect: over-engineering pelos drivers atuais.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- tests/test_epic.py: 10/10 passed (numeracao independente; --under cria filho; recusa parent inexistente/nao-epic; arvore agregada + epic vazio; finish recusa filhos abertos; libera com cancelados; cancel sem cascata). Suite completa: 176 passed (166 + 10). render --check OK (61 alvos: +commands/epic.md + .agents/skills/guia-epic). doctor OK.

### Validacao pendente

- Nenhuma.

## [D-067] ✨ Dependencia entre demandas (so executa apos concluir)

- **Status:** Validada
- **Origem:** Backlog (2026-06-11)
- **Tipo:** Feature
- **Contexto:** Permitir que uma demanda declare dependencia de outra(s) (ex: D-065 depende de D-066). A demanda dependente fica bloqueada para execucao ate que a demanda da qual depende seja concluida (status Concluida). O start/promote deve recusar iniciar enquanto a dependencia nao fechar, e idealmente listar/visualizar a cadeia de dependencias. Caso de uso real: as 4 skills D-063..D-066 ja tem relacao de pre-requisito entre si.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_constants.py`
- `core/src/_tasks.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_creation.py`
- `core/src/_cli_deps.py`
- `core/src/guia.py`
- `tests/test_depends.py`
- `docs/reference/cli.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_tasks.py`
- `plugins/guia/bin/guia.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-22: Onda 2 leftover: dependencia entre demandas (bloqueia start/promote ate dep fechar).
- D-067 implementado de ponta a ponta. Modelo: campo 'dependsOn: [D-XYZ, ...]' por task; STATUSES_SATISFY_DEPENDENCY = {Validada, Finalizada, Resolvida, Cancelada} (Cancelada conta - dep terminada explicitamente nao deve travar a dependente). Bloqueio em start (cmd_start) e promote (cmd_promote, so para source=tasks); ready/finish ficam livres (ja existe). Declaracao: --depends-on D-X (repetivel) em feature/bug/chore. Subcomando dedicado 'depends add/remove/list <id>' com --on D-X (repetivel). Recusa auto-dep, id inexistente e ciclos (DFS sobre o grafo). Novo modulo core/src/_cli_deps.py irmao de _cli_creation.py.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- tests/test_depends.py: 11/11 passed (declaracao com multiplas deps; dedup preservando ordem; bloqueio em start; libera apos finish; cancel da dep tambem libera; add-remove roundtrip; auto-dep recusada; id inexistente recusado; ciclo detectado; list --json marca blocking; lista vazia). Suite completa: 166 passed (155 + 11). render --check OK (59 alvos). doctor OK.

### Validacao pendente

- Nenhuma.

## [D-091] ✨ guia:upgrade - migrar projetos existentes para o layout atual

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-21)
- **Tipo:** Feature
- **Contexto:** Comando idempotente que detecta layout antigo e migra: (a) FEATURES.md na raiz -> .guia/DEMANDAS.md; (b) features/registry.yaml -> .guia/locks/registry.yaml; (c) features/lock-ignore.txt -> .guia/locks/lock-ignore.txt; (d) remove features/ se ficou vazio. Sem perder nada (rename, nao copy+delete). --dry-run lista o plano sem mutar; default executa. Distinto de /plugin update (que atualiza o plugin) e de backlog migrate (que mexe em backlog.json). Emite NOOP se ja esta atualizado. Comando determinista no guia.py; teste com fixture do layout antigo + asserts pos-migracao.

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/upgrade.md`
- `tests/test_upgrade.py`
- `docs/reference/cli.md`
- `CLAUDE.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/guia.py`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Step 3 do par estrutural: 'guia upgrade' (verbo + skill /guia:upgrade) migra projetos do layout antigo (FEATURES.md + features/ na raiz) para o atual (.guia/DEMANDAS.md + .guia/locks/). Implementacao: cmd_upgrade em _cli_lifecycle.py com plano + git mv quando possivel (preserva historico de rename) + fallback shutil.move; remove features/ se vazio. Idempotente (NOOP quando nada a mover); --dry-run lista sem mutar; recusa (exit 1) se destino ja existe (resolva a mao). Adicionado a _NO_AUTO_INIT (nao auto-cria .guia/ antes de migrar). Verbo no manifest -> render gerou /guia:upgrade + skill cross-tool. Docs: cli.md (secao 'upgrade'), CLAUDE.md (tabela).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- tests/test_upgrade.py: 5/5 passed (NOOP, dry-run sem mutacao, migra-preservando-conteudo, idempotente apos migracao, recusa quando destino existe). Suite completa: 155 passed (era 150 + 5). render --check OK (58 alvos). doctor OK.

### Validacao pendente

- Nenhuma.

## [D-056] ✨ Racionalizar estrutura de pastas: features/ para dentro de .guia/, clarificar separacao ferramenta-vs-dados

- **Status:** Validada
- **Origem:** Backlog (2026-06-09)
- **Tipo:** Feature
- **Contexto:** Tres problemas identificados: (1) features/ (registry.yaml + lock-ignore.txt) esta na raiz do projeto consumidor, mas e dado do processo da ferramenta - deveria estar em .guia/features/ ou .guia/locks/ junto do restante do processo. Hoje REGISTRY_FILE = ROOT / 'features' / 'registry.yaml' em _constants.py. Mover exige: atualizar _constants.py, atualizar install.ps1, atualizar docs/reference/files.md, migrar projetos existentes. (2) Confusao sobre o que e ferramenta vs dados: no repo-fonte, dist/ serve diretamente como plugin via extraKnownMarketplaces - o usuario-dev nao ve .guia-fluxo/ porque esta dentro do proprio repo. No projeto consumidor, install.ps1 cria .guia-fluxo/ (ferramenta) e .guia/ (dados). Essa distincao nao esta documentada claramente no README/CONTRIBUTING. (3) Suficiencia para operacao: .agents/skills/ + .claude-plugin/ nao sao suficientes sozinhos - bin/ (motor Python) e obrigatorio para execucao real. O doctor deveria checar se bin/ existe no layout consumidor e alertar quando falta. Escopo da tarefa: mover features/ para .guia/features/, atualizar todos os caminhos, adicionar verificacao no doctor, atualizar docs descrevendo os dois contextos (dev vs consumidor).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/lock/lock_api.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_locks.py`
- `core/lock/check-lock.py`
- `core/build/render-skills.py`
- `core/hooks/commit-msg`
- `core/manifest/manifest.yaml`
- `.guia/locks/registry.yaml`
- `.guia/locks/lock-ignore.txt`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `README.md`
- `SECURITY.md`
- `core/manifest/bodies/_partials/lock_protocol.md`
- `core/manifest/bodies/guia-fluxo.md`
- `core/templates/locks/lock-ignore.txt`
- `core/templates/locks/registry.yaml`
- `docs/explanation/por-que-lock.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/editar-arquivo-travado.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/travar-arquivo.md`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `docs/reference/hooks-git.md`
- `docs/reference/registry-yaml.md`
- `docs/tutorials/primeiro-uso.md`
- `plugins/guia/.agents/skills/guia-bug/SKILL.md`
- `plugins/guia/.agents/skills/guia-chore/SKILL.md`
- `plugins/guia/.agents/skills/guia-feature/SKILL.md`
- `plugins/guia/.agents/skills/guia-finish/SKILL.md`
- `plugins/guia/.agents/skills/guia-fluxo/SKILL.md`
- `plugins/guia/.agents/skills/guia-init/SKILL.md`
- `plugins/guia/.agents/skills/guia-promote/SKILL.md`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_locks.py`
- `plugins/guia/bin/check-lock.py`
- `plugins/guia/bin/lock_api.py`
- `plugins/guia/commands/bug.md`
- `plugins/guia/commands/chore.md`
- `plugins/guia/commands/feature.md`
- `plugins/guia/commands/finish.md`
- `plugins/guia/commands/guia-fluxo.md`
- `plugins/guia/commands/init.md`
- `plugins/guia/commands/promote.md`
- `plugins/guia/templates/.githooks/commit-msg`
- `tests/test_init_deploy.py`
- `tests/test_render_hardening.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-21: Step 1 do par estrutural: features/ -> .guia/locks/.
- Step 1 do par estrutural: features/ -> .guia/locks/ (decisao: nome 'locks' mais honesto). Paths em _constants.REGISTRY_FILE, lock_api.REGISTRY/LOCK_IGNORE, init deploy (_cli_lifecycle), TEMPLATE_FILES (render). Movidos via git mv: features/{registry.yaml,lock-ignore.txt} -> .guia/locks/, e core/templates/features/ -> core/templates/locks/. Strings funcionais (_locks exclude, modifiedFiles) e display (check-lock, mensagens) corrigidas. Re-render. Varredura de ~18 docs vivos + manifest (subagente). Testes test_init_deploy + test_render_hardening ajustados.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- LOCK testado no novo path: bloqueia add sem unlock (exit 1), libera com [unlock:] (exit 0). pytest 150 passed. render --check OK. doctor OK. grep: zero refs vivas a features/.

### Validacao pendente

- Nenhuma.

## [D-055] ✨ Renomear FEATURES.md e implementar arquivamento de demandas antigas

- **Status:** Validada
- **Origem:** Backlog (2026-06-09)
- **Tipo:** Feature
- **Contexto:** Dois problemas: (1) Nome 'FEATURES.md' nao reflete a realidade atual - o arquivo guarda features, bugs e chores (o guarda-chuva e 'demanda'). Candidatos: DEMANDAS.md, HISTORICO.md, DEMANDS.md. (2) Tamanho: o arquivo cresce indefinidamente. Hoje tem 122KB com 52+ demandas e vai piorar. Custo real: agente carregando o arquivo inteiro no contexto a cada operacao. Solucao proposta: manter somente as N ultimas demandas (parametro em process.json, default 20-30) no arquivo ativo; mover demandas mais antigas para DEMANDAS.archive.md (ou .guia/historico/YYYY-MM.md). Para o bloqueio de leitura por IA: adicionar uma linha no topo do arquivo de arquivo como '<!-- guia-fluxo: archive=true ai-skip=true -->' que o agente pode verificar antes de carregar. Impacto tecnico: _features_md.py (upsert_features_entry), _tasks.py (format/display), _constants.py (path do arquivo). Avaliar se FEATURES.md fica na raiz ou vai para .guia/ junto dos outros arquivos de processo.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_tasks.py`
- `core/src/_locks.py`
- `core/src/_cli_creation.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_features_md.py`
- `.guia/docs-map.yaml`
- `.guia/DEMANDAS.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `README.md`
- `SECURITY.md`
- `core/manifest/bodies/_partials/title_context_rules.md`
- `core/manifest/bodies/block.md`
- `core/manifest/bodies/cancel.md`
- `core/manifest/bodies/plan.md`
- `core/manifest/bodies/start.md`
- `docs/README.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/reference/cli.md`
- `docs/reference/docs-map.md`
- `docs/reference/files.md`
- `docs/tutorials/primeiro-uso.md`
- `plugins/guia/.agents/skills/guia-backlog/SKILL.md`
- `plugins/guia/.agents/skills/guia-block/SKILL.md`
- `plugins/guia/.agents/skills/guia-bug/SKILL.md`
- `plugins/guia/.agents/skills/guia-cancel/SKILL.md`
- `plugins/guia/.agents/skills/guia-chore/SKILL.md`
- `plugins/guia/.agents/skills/guia-feature/SKILL.md`
- `plugins/guia/.agents/skills/guia-plan/SKILL.md`
- `plugins/guia/.agents/skills/guia-start/SKILL.md`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_features_md.py`
- `plugins/guia/bin/_locks.py`
- `plugins/guia/bin/_tasks.py`
- `plugins/guia/commands/backlog.md`
- `plugins/guia/commands/block.md`
- `plugins/guia/commands/bug.md`
- `plugins/guia/commands/cancel.md`
- `plugins/guia/commands/chore.md`
- `plugins/guia/commands/feature.md`
- `plugins/guia/commands/plan.md`
- `plugins/guia/commands/start.md`
- `tests/test_tasks_domain.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-21: Onda 2 (destravada pelo spike D-058): renomear FEATURES.md + arquivamento; coordenar com D-056 (mover features/ -> .guia/).
- Rename+move: FEATURES.md (raiz) -> .guia/DEMANDAS.md (decisao: nome reflete 'demanda', e raiz do consumidor fica so com .guia/, cumprindo o global-first junto do D-056). Constantes FEATURES_FILE/FEATURES_HEADER ajustadas; header do arquivo -> '# Demandas'. Fix funcional: nova const FEATURES_REL (path root-relativo .guia/DEMANDAS.md) usada em new_task/promote/start/exclusao-de-lock - antes era basename, que quebraria o commit (git stageia .guia/DEMANDAS.md). docs-map.yaml e manifest bodies (block/cancel/plan) atualizados; PR template; comentarios de codigo.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- 150 testes; render --check OK; doctor OK; zero refs vivas a FEATURES.md (so historico/fixtures).

### Validacao pendente

- Nenhuma.

## [D-083] ✨ Primitiva de servicos (guia service): ADR + design do 3o dominio

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-20)
- **Tipo:** Feature
- **Contexto:** Design+ADR de uma primitiva de servicos que unifica D-062/064/065/066/063 (todas sao 'orquestrar um conjunto configurado de skills com prompt/criterio'). Formaliza o modelo de dominio do Guia Fluxo em 3 grandes grupos: Demandas, Locks, Servicos. Servico = receita de orquestracao (quais skills, ordem, prompt de config, saida); skills vivem externas (Claude/Codex); guia e dono da receita. CRUD deterministico (guia service add/edit/remove/list/show/run) espelhando locks; catalogo .guia/services.yaml = dado do consumidor (plugin fica com a cara dele); execucao agent-driven via /guia:service <nome>. Estrategia: ADR primeiro, depois construir pequeno (CRUD + 1 servico real). Esta demanda entrega o ADR; implementacao vira demanda separada.

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/adr/0016-primitiva-de-servicos.md`
- `docs/adr/README.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `README.md`
- `core/manifest/bodies/guia-fluxo.md`
- `core/src/_constants.py`
- `docs/ROADMAP.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/tutorials/primeiro-uso.md`
- `plugins/guia/.agents/skills/guia-fluxo/SKILL.md`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/commands/guia-fluxo.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- ADR-0016 (Proposta): primitiva de servicos como 3o dominio (Demandas/Locks/Servicos). Servico = receita de orquestracao (skills externas + prompt + saida); CRUD deterministico guia service espelhando locks; catalogo .guia/services.yaml do consumidor; execucao agent-driven /guia:service; cross-tool via manifest->render. Mapeia D-066=primitiva, D-065/064/062/063=servicos. Estrategia faseada (MVP: CRUD + valida-pasta). Tambem adicionei ao indice o 0015 que faltava (drift do D-076).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- Sem codigo (so docs/adr). ADR segue o template (Contexto/Decisao/Consequencias/Alternativas/Links).

### Validacao pendente

- Nenhuma.

## [D-082] ✨ install.ps1 e install.sh quebrados: apontam dist/ (removido no D-076)

- **Status:** Validada
- **Origem:** Backlog (2026-06-20)
- **Tipo:** Feature
- **Contexto:** Confirmado no spike D-058 (2026-06-20): install.ps1 (linha 66 DistRoot=repo/dist + throw 68-70) e install.sh (DIST_ROOT linha 70 + exit 1 73-74) abortam com 'dist/ nao encontrado' porque o D-076 renomeou dist/ -> plugins/guia/. install.ps1 -DryRun aborta na hora. A rota install.* (Codex/Antigravity/dev, conforme CHANGELOG D-075) esta morta. Decidir: (a) corrigir DistRoot -> plugins/guia e ajustar o layout copiado + doc embutida (o consumidor copiaria plugins/guia em vez de dist); OU (b) deprecar formalmente os installers, ja que o global-first (/plugin install + auto-init + /guia:init) e o caminho canonico. Relacionado a D-056 (estrutura de pastas) e D-060.

### Arquivos modificados/criados

- `FEATURES.md`
- `install.ps1`
- `install.sh`
- `tests/test_install.py`
- `README.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/tutorials/primeiro-uso.md`
- `docs/ROADMAP.md`
- `docs/explanation/visao-geral.md`
- `core/manifest/bodies/guia-fluxo.md`
- `core/src/_constants.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/commands/guia-fluxo.md`
- `plugins/guia/.agents/skills/guia-fluxo/SKILL.md`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `docs/adr/README.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-20: Deprecar install.ps1/.sh (quebrados, apontam dist/); global-first + copia-manual cobrem; cross-tool formaliza no B-004.
- Deprecados install.ps1/.sh (quebrados desde D-076, confirmado no spike D-058). Removidos os 2 scripts + tests/test_install.py. Docs reescritos p/ global-first (Claude) + copia-manual (Codex/Antigravity, automacao em aberto B-004): README, how-to (reescrito), tutorial, manifest body (re-render), anotacoes historicas ROADMAP/visao-geral. Corrigido tambem stale do marketplace.json interno no body (removido no D-077). Resolvidos D-060 (hooksPath ja guardado por init) e D-061 (bug original resolvido; gap residual no relatorio do spike).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- render --check OK; doctor OK; pytest 150 passed (test_install.py removido)

### Validacao pendente

- Nenhuma.

## [D-058] ✨ Spike: instalar em projeto-teste e mapear experiencia real do consumidor

- **Status:** Validada
- **Origem:** Backlog (2026-06-10)
- **Tipo:** Feature
- **Contexto:** Objetivo: antes de implementar D-055 (renomear FEATURES.md), D-056 (mover features/ para .guia/) e D-057 (rename de chat), criar um projeto-teste vazio e rodar install.ps1 nele para ver exatamente o que o usuario recebe hoje. Isso serve dois propositos: (1) Validar o que funciona e o que esta estranho na visao do consumidor - quais pastas aparecem, o que o Claude Code detecta, se o doctor passa, se as skills disparam, se o fluxo feature -> ready -> finish funciona end-to-end. (2) Usar a experiencia real para priorizar e detalhar os backlogs estruturais (D-053, D-055, D-056) com evidencias concretas em vez de suposicoes. Passos sugeridos: (a) criar pasta vazia em algum lugar fora do repo-mae (ex: C:/dev/guia-teste); (b) rodar: .\install.ps1 -Target C:/dev/guia-teste -DryRun para previa; (c) rodar sem DryRun; (d) abrir o projeto no Claude Code e verificar se o plugin e detectado; (e) criar uma demanda de teste, rodar ready + finish; (f) documentar o que ficou confuso, o que estava faltando, o que soou errado no nome/layout. Resultado esperado: lista de ajustes priorizados que alimenta D-053/D-055/D-056 com contexto real.

### Arquivos modificados/criados

- `FEATURES.md`
- `.guia/reports/D-058-spike-consumidor.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `README.md`
- `core/manifest/bodies/guia-fluxo.md`
- `core/src/_constants.py`
- `docs/ROADMAP.md`
- `docs/adr/README.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/tutorials/primeiro-uso.md`
- `plugins/guia/.agents/skills/guia-fluxo/SKILL.md`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/commands/guia-fluxo.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-20: Spike: instalar em projeto-teste vazio e mapear a experiencia real do consumidor pos-global-first (D-076).
- Spike empirico: plugin isolado + projeto vazio, simulando o consumidor global-first. RESULTADO: o fluxo global-first FUNCIONA end-to-end (auto-init, /guia:init deploya locks/hook, doctor OK, feature->ready->finish, hook bloqueia/libera corretamente com CLAUDE_PLUGIN_ROOT). 3 achados: (1) install.ps1/.sh QUEBRADOS (apontam dist/ removido no D-076) -> D-082; (2) D-061 bug original RESOLVIDO pelo global-first, resta so o gap de locks nao valerem fora de sessao Claude; (3) D-060 ja coberto por init (so falta doc). Warts: doctor pre-init cospe FAIL com exit 0.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- Testado em projeto isolado: doctor, feature, init (locks+hooksPath), ready, finish; hook commit-msg nos 2 modos (com/sem CLAUDE_PLUGIN_ROOT) + unlock

### Validacao pendente

- Nenhuma.

## [D-077] ✨ Corrigir source '../' no marketplace.json interno do plugin (alinhar codex-plugin-cc)

- **Status:** Validada
- **Origem:** Backlog (2026-06-19)
- **Tipo:** Feature
- **Contexto:** plugins/guia/.claude-plugin/marketplace.json declara o plugin com source: '../', mas a doc do Claude Code recomenda NAO usar '../' em source de plugin (deve ser caminho relativo ao marketplace root comecando com './'). Latente: so morde no install por marketplace LOCAL directory (que a versao atual do Claude do dev nem suporta); o caminho GitHub usa o marketplace.json da raiz (source './plugins/guia', correto). Opcao: alinhar 1:1 ao codex-plugin-cc - marketplace.json so na raiz, settings.json do repo apontando para '.' em vez de './plugins/guia', e remover/ajustar o marketplace.json interno. Descoberto na D-076 ao diagnosticar erro de install local (source type not supported).

### Arquivos modificados/criados

- `FEATURES.md`
- `.claude/settings.json`
- `CLAUDE.md`
- `plugins/guia/.claude-plugin/marketplace.json`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CONTRIBUTING.md`
- `core/src/_cli_creation.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_constants.py`
- `core/src/guia.py`
- `docs/reference/cli.md`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/guia.py`

### O que foi feito

- Em desenvolvimento desde 2026-06-20: Onda 1: limpar marketplace interno (dev-loop).
- Dev-loop: removido o marketplace.json interno de plugins/guia/.claude-plugin/ (usava source '../' desaconselhado). settings.json extraKnownMarketplaces repontado de ./plugins/guia para '.' (le o marketplace.json da raiz). CLAUDE.md atualizado. Teste local agora: abrir o repo (descoberta via raiz) ou claude --plugin-dir ./plugins/guia (carrega direto, sem marketplace).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- render-skills.py --check: 56 alvos OK (marketplace interno nao e gerado)

### Validacao pendente

- Nenhuma.

## [D-079] 🧹 Subcomando backlog resolve para retirar item de backlog ja entregue

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-20)
- **Tipo:** Chore
- **Contexto:** Nao ha caminho oficial para retirar do backlog um item ja entregue por outra demanda (skill backlog so tem add/list/migrate/promote). Resultado: itens zumbis poluindo backlog list. Criar subcomando deterministico 'backlog resolve <id> [--reason]' que marca o item (tasks.json status=Backlog OU backlog.json legacy) como Resolvida + resolvedAt + resolution, e some do backlog list. Usar para fechar B-009/B-011/B-017 (ja entregues: marketplace remoto, cancel, plan).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_cli_creation.py`
- `core/src/guia.py`
- `plugins/guia/bin/_constants.py`
- `plugins/guia/bin/_cli_creation.py`
- `plugins/guia/bin/guia.py`
- `tests/test_backlog_resolve.py`
- `docs/reference/cli.md`
- `.guia/backlog.json`
- `core/src/_cli_lifecycle.py`
- `plugins/guia/bin/_cli_lifecycle.py`
- `CONTRIBUTING.md`
- `tests/test_status_all.py`
- `.claude/settings.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CLAUDE.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Novo subcomando deterministico 'backlog resolve <id> [--reason]' (status STATUS_RESOLVED=Resolvida) que retira do backlog ativo item ja entregue/obsoleto nas duas fontes (tasks.json D-NNN + backlog.json legacy B-NNN), preservando para historico. backlog list filtra resolvidos. Usado para fechar B-009/B-011/B-017.
- BUNDLE Onda 1 (3 itens). (1) D-079 backlog resolve: subcomando deterministico 'backlog resolve <id> [--reason]' (STATUS_RESOLVED) nas 2 fontes; fechou B-009/B-011/B-017. (2) B-014 status --all: quadro de tasks Em desenvolvimento + aviso de concorrencia B-018 quando ha 2+ ativas. (3) D-078: F-NNN/I-NNN->D-NNN nos exemplos de CONTRIBUTING.md e cli.md (legacy statements preservados).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- pytest tests/test_backlog_resolve.py: 4 passed
- pytest tests/ (suite completa): 150 passed
- guia doctor: exit 0 / render-skills.py --check: 56 alvos em sincronia
- pytest tests/: 153 passed
- guia doctor: exit 0; render-skills.py --check: 56 alvos OK

### Validacao pendente

- Nenhuma.

## [D-076] ✨ Plugin global-first + guia:init (ref codex-plugin-cc)

- **Status:** Validada
- **Origem:** Backlog D-076 promovido (2026-06-17)
- **Tipo:** Feature
- **Contexto:** Convergir para arquitetura plugin-global-first espelhando openai/codex-plugin-cc: motor+skills+templates 100% no plugin global (CLAUDE_PLUGIN_ROOT), projeto do cliente so com estado/controle (.guia/ JSONs + FEATURES.md + lock/hook opcionais). Adicionar /guia:init. Limpar o que nao e necessario (provavel: install.ps1/sh, layout .guia-fluxo no consumidor, talvez .agents cross-tool). Decisoes abertas: E1 nome da pasta local (.guia vs .guia-fluxo), E2 fate de Codex/Antigravity, E3 manter core/dist+render ou reestruturar, E4 escopo do guia:init (deploy de templates + hooksPath). Continua o D-075 (que ja poe o motor no plugin global via CLAUDE_PLUGIN_ROOT, auto-init, raiz por CWD).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/_state.py`
- `core/src/guia.py`
- `core/src/_constants.py`
- `core/src/_locks.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `core/hooks/commit-msg`
- `core/build/render-skills.py`
- `core/bin/guia`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/init.md`
- `core/manifest/bodies/guia-fluxo.md`
- `core/manifest/bodies/_partials/README.md`
- `.claude/settings.json`
- `.claude-plugin/marketplace.json`
- `docs/adr/0015-plugin-global-first-guia-init.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `tests/test_init_deploy.py`
- `tests/test_install.py`
- `tests/test_manifest_layout_b.py`
- `tests/test_body_partials.py`
- `tests/test_render_includes.py`
- `plugins/guia/skills/init/SKILL.md`
- `plugins/guia/.agents/skills/guia-init/SKILL.md`
- `plugins/guia/bin/check-lock.py`
- `plugins/guia/commands/init.md`
- `plugins/guia/commands/feature.md`
- `SECURITY.md`
- `tests/test_render_polish.py`
- `tests/test_render_hardening.py`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `tests/test_lock_api.py`

### O que foi feito

- Backlog D-076 promovido via guia-fluxo.
- Avaliacao IA: Demanda valida e bem escopada. O caminho Claude ja e plugin-global-first (D-075: no-clone, motor via CLAUDE_PLUGIN_ROOT, raiz por CWD, auto-init de .guia/). Decisoes fechadas com o dev: E1 manter .guia/; E2 preservar cross-tool (Codex/Antigravity) intacto e tratar em demanda separada; E3 renomear dist/ -> plugins/guia/; E4 /guia:init full. Net-new: /guia:init + rename de layout + docs/ADR-0015. Sem worktree, in-place no main.
- Convergencia plugin-global-first (espelha codex-plugin-cc). (1) Novo verbo/skill init (/guia:init) FULL: semeia .guia/ + deploya templates de lock (features/registry.yaml, lock-ignore.txt, .githooks/commit-msg) do plugin + git core.hooksPath; idempotente, no-clobber, flag --no-locks. Reusa initialize_project (D-075); fonte dos templates via CLAUDE_PLUGIN_ROOT/templates com fallback <engine>/../templates.
- (2) Rename dist/ -> plugins/guia/ (git ve como renomeacao): default do Paths.build em render-skills.py, .claude/settings.json (extraKnownMarketplaces ./plugins/guia), .claude-plugin/marketplace.json raiz (source), doctor, e testes que hardcodavam dist (test_install/manifest_layout_b/body_partials/render_includes). marketplace.json dentro do plugin usa source ../ e seguiu valido.
- (3) Locks funcionais no consumidor plugin-global: lock_api.REPO_ROOT em 3 camadas (GUIA_PROJECT_ROOT > script-se-tem-.guia > CWD, espelha _constants); check-lock.py embarcado no bin do plugin; commit-msg robusto (descobre validador em core/lock OU CLAUDE_PLUGIN_ROOT/bin, degrada exit 0 com aviso se nenhum).
- (4) Cross-tool Codex/Antigravity (target agent_skill, .agents/skills, install.ps1/.sh, .guia-fluxo/) PRESERVADO intacto e adiado para demanda separada (decisao E2). Docs: ADR-0015 (novo), README, instalar-em-outro-projeto, body guia-fluxo, cli.md, files.md, AGENTS/CLAUDE, CONTRIBUTING, CHANGELOG. visao-geral.md mantido com refs dist/ historicas (F-011/F-012) de proposito.
- ARQUIVOS NOVOS exigem no commit: [unlock:adicoes-exigem-autorizacao] motivo: <razao> (alem da palavra motivo:). Novos: core/manifest/bodies/init.md, docs/adr/0015-*.md, tests/test_init_deploy.py, plugins/guia/skills/init/SKILL.md, plugins/guia/.agents/skills/guia-init/SKILL.md, plugins/guia/bin/check-lock.py.
- AJUSTE pos-validacao (skills -> commands): plugin SKILLS surgem bare no menu de slash (/init, /bug) e colidem com built-ins (/init) - confirmado pelo dev no install real. Migrado o target Claude de Agent Skills (skills/<verbo>/SKILL.md) para plugin COMMANDS (commands/<verbo>.md): render-skills.py ganha TargetSpec.emits_command + output flat sem 'name:' (claude_command); manifest key claude_skill->claude_command nos 15 verbos; plugins/guia/skills/ removido; commands/ gerado. Resultado: verbos namespaced /guia:<verbo>, sem colisao, auto-trigger por description preservado. Target agent_skill (Codex/Antigravity, .agents/skills/) intacto.
- Docs alinhados (claude=commands, agent=skills): CLAUDE.md, AGENTS.md, CONTRIBUTING.md, docs/reference/{cli,files}.md, SECURITY.md, body guia-fluxo, ADR-0015 (decisao #4 + consequencias), CHANGELOG. 6 testes atualizados (body_partials/manifest_layout_b/render_includes/render_polish/render_hardening/install). Revisao adversarial (3 agentes) limpa: so 1 stale real (AGENTS.md:11 skills->commands) corrigido; resto pre-existente fora de escopo.
- Fechada via finish --no-commit + commit manual unico: o commit_task do motor so cobre task.modifiedFiles e nao injeta o marcador [unlock:adicoes-exigem-autorizacao] que os arquivos novos exigem.

### Validacao feita

- python core/build/render-skills.py --check -> OK 56 alvos em sincronia
- python -m pytest -> 144 passed (inclui tests/test_init_deploy.py novo: deploy templates + hooksPath + idempotencia/no-clobber + --no-locks)
- python core/src/guia.py doctor -> Guia Fluxo files OK
- hook commit-msg testado ao vivo no repo-mae: bloqueia add sem marcador (exit 1), libera com [unlock] + motivo (exit 0)
- check-lock.py do plugin rodado de tmpdir resolve a raiz por CWD (reporta 'Nenhuma trava ativa' do tmp, nao o registry do repo) -> locks valem no consumidor
- Dev confirmou no ambiente real (claude --plugin-dir + /reload-plugins): /guia:bug e /guia:init aparecem NAMESPACED, /guia filtra os verbos, /init nativo livre. Screenshots.
- render --check OK (56 alvos); pytest 144 passed; doctor OK (apos a migracao)
- render --check OK (56 alvos); pytest 146 passed (inclui lock_api _resolve_repo_root e test_init_deploy); doctor OK; /guia:* namespaced confirmado pelo dev no ambiente real (claude --plugin-dir + reload)

### Validacao pendente

- Nenhuma.

## [D-075] ✨ Plugin autossuficiente: install sem clone (CLAUDE_PLUGIN_ROOT)

- **Status:** Aguardando validacao
- **Origem:** Guia Fluxo (2026-06-16)
- **Tipo:** Feature
- **Contexto:** Tornar /plugin install guia@guia-fluxo suficiente sozinho (sem clone nem install.ps1) para usuarios Claude Code. Hoje as skills mandam rodar .\core\bin\guia.ps1 (relativo ao CWD) - exatamente o que a doc oficial plugin-dev proibe; o certo e a env var CLAUDE_PLUGIN_ROOT. O motor ja esta empacotado standalone em dist/bin/guia.py (F-012) e o plugin source e ./dist, entao CLAUDE_PLUGIN_ROOT = dist instalado -> python no bin do plugin funciona. Escopo Completo: (1) run command host-aware (Claude -> CLAUDE_PLUGIN_ROOT/bin/guia.py; agent Codex/Antigravity mantem deploy install.sh), (2) auto-init do .guia no 1o uso, (3) README/docs do fluxo sem clone + pre-req Python 3.10+. Relaciona spike D-058.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/bodies/_partials/run_cmd.claude.md`
- `core/manifest/bodies/_partials/run_cmd.agent.md`
- `core/manifest/bodies/feature.md`
- `core/manifest/bodies/bug.md`
- `core/manifest/bodies/chore.md`
- `core/manifest/bodies/backlog.md`
- `core/manifest/bodies/block.md`
- `core/manifest/bodies/cancel.md`
- `core/manifest/bodies/finish.md`
- `core/manifest/bodies/plan.md`
- `core/manifest/bodies/promote.md`
- `core/manifest/bodies/ready.md`
- `core/manifest/bodies/start.md`
- `core/manifest/bodies/status.md`
- `core/manifest/bodies/unblock.md`
- `core/manifest/bodies/guia-fluxo.md`
- `tests/test_auto_init.py`
- `tests/test_body_partials.py`
- `tests/test_manifest_layout_b.py`
- `README.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/adr/0014-plugin-autossuficiente-claude-plugin-root.md`
- `docs/adr/README.md`
- `CHANGELOG.md`
- `dist/ (regenerado por render-skills.py: skills/*, .agents/skills/*, bin/_constants.py, bin/_cli_lifecycle.py, bin/guia.py)`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Em desenvolvimento desde 2026-06-16.
- Parte 1 (run host-aware): novo partial _partials/run_cmd.{claude,agent}.md incluido via {{include_per_target}} em TODOS os 13 verbos + Core Rule do guia-fluxo. Claude invoca python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command> (bash canonico + nota PowerShell $env:); agent mantem core/bin/guia.ps1 + fallback core/src/guia.py (sem regressao). Refs secundarias (block 'To resume', Portable install) neutralizadas.
- Parte 2 (auto-init + raiz CWD): _constants.ROOT agora resolve em camadas (GUIA_PROJECT_ROOT > script_root quando ja tem .guia/ > CWD exato, SEM walk-up ancestral pra nao sequestrar .guia de pai). _cli_lifecycle.initialize_project()+ensure_initialized() extraidos de cmd_init; guia.py chama ensure_initialized() antes do dispatch (denylist init/doctor/render). NECESSARIO porque o plugin instalado vive fora da arvore do projeto: so __file__.parents[2] criaria .guia no cache.
- Parte 3 (docs): README Instalacao lidera com rota sem clone (Python 3.10+); how-to instalar-em-outro-projeto com secao sem-clone; ADR-0014 novo + indice ADR; secao Portable install do body guia-fluxo reescrita; CHANGELOG [Unreleased] com a nuance dogfood (skills ativas vem de ./dist -> agente invoca dist/bin/guia.py; quem dev o motor usa core/bin/guia.ps1).
- ARQUIVOS NOVOS (lock 'adicoes-exigem-autorizacao', op add): run_cmd.claude.md, run_cmd.agent.md, tests/test_auto_init.py, docs/adr/0014-*.md. O COMMIT (feito por voce) vai precisar de [unlock:adicoes-exigem-autorizacao] motivo: <razao>.

### Validacao feita

- python core/build/render-skills.py && --check verde (53 alvos em sincronia)
- python -m pytest: 141 passed (inclui tests/test_auto_init.py novo: roota no CWD, aviso auto-init, doctor nao auto-inicializa, override GUIA_PROJECT_ROOT)
- python core/src/guia.py doctor: Guia Fluxo files OK
- Simulacao real: copiei dist/bin pra fora do repo, rodei de um projeto temp -> auto-init disparou, D-001 fresh criado no projeto, .guia NAO vazou pra pasta do motor

### Validacao pendente

- Validacao humana: num projeto NOVO (sem clone) rodar /plugin marketplace add Paulo-Marcos/guia-fluxo + /plugin install guia@guia-fluxo e depois /guia:feature "teste" pra confirmar o motor via ${CLAUDE_PLUGIN_ROOT}
- Commit (humano) com [unlock:adicoes-exigem-autorizacao] por causa dos 4 arquivos novos

## [D-074] ✨ B-009: marketplace remoto (.claude-plugin na raiz)

- **Status:** Aguardando validacao
- **Origem:** Guia Fluxo (2026-06-16)
- **Tipo:** Feature
- **Contexto:** Front #3 Akita. Repo publico. /plugin marketplace add Paulo-Marcos/guia-fluxo exige (guia oficial) .claude-plugin/marketplace.json na RAIZ - so existe em dist/. Criar root marketplace.json aditivo, plugin source ./dist (dogfood local segue ./dist via settings). Corrigir snippet install no README (/plugin install guia@guia-fluxo - plugin name e guia). Marcar B-009 entregue em ROADMAP/visao-geral. Drift namespace ai->guia fica chore separado. Validacao final e do dev em sessao Claude Code nova.

### Arquivos modificados/criados

- `FEATURES.md`
- `.claude-plugin/marketplace.json`
- `README.md`
- `docs/ROADMAP.md`
- `docs/explanation/visao-geral.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- B-009: criado .claude-plugin/marketplace.json na raiz (plugin guia, source ./dist) habilitando /plugin marketplace add Paulo-Marcos/guia-fluxo remoto (guia oficial exige o manifest na raiz). README install snippet corrigido (/plugin install guia@guia-fluxo). ROADMAP/visao-geral marcam B-009 entregue. Aditivo: dogfood local segue ./dist.

### Validacao feita

- marketplace.json JSON valido; doctor verde; render --check verde (53)

### Validacao pendente

- Humano: validar /plugin marketplace add Paulo-Marcos/guia-fluxo + /plugin install guia@guia-fluxo numa sessao Claude Code nova

## [D-073] 🧹 Release v0.2.0: cortar CHANGELOG, bump VERSION, release.yml

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-15)
- **Tipo:** Chore
- **Contexto:** Front #2 do mapeamento Akita. Repo publicado e CI verde. (1) CHANGELOG [Unreleased] -> [0.2.0] - 2026-06-15 consolidando D-068/069/070/071/072. (2) VERSION 0.1.0 -> 0.2.0 (alinha plugin.json/marketplace.json ja em 0.2.0). (3) release.yml: workflow de release por tag v* (render --check + gh release create --generate-notes). Tag v0.2.0 + push e o passo outward-facing final com OK do dev. release.yml e arquivo novo -> commit precisa de [unlock:adicoes-exigem-autorizacao].

### Arquivos modificados/criados

- `FEATURES.md`
- `CHANGELOG.md`
- `VERSION`
- `.github/workflows/release.yml`
- `README.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Release v0.2.0: CHANGELOG [Unreleased]->[0.2.0] 2026-06-15 (consolida D-068..D-072); VERSION 0.1.0->0.2.0; release.yml (release por tag v*: render --check + gh release create --generate-notes); badges de status (tests, render-check, release, MIT) no topo do README.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- doctor verde; render --check verde (53 alvos); release.yml YAML valido

### Validacao pendente

- Nenhuma.

## [D-072] 🐛 render-skills: include guard usa manifest_dir nao-resolvido (quebra CI Windows)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-15)
- **Tipo:** Bug / regressao
- **Contexto:** CI Windows (GitHub Actions) falhou no primeiro push: tests/test_render_includes.py::GuardTests::test_circular_include_detected estoura ValueError em vez de RenderError. Causa em core/build/render-skills.py:393: ao montar o chain do include circular, p.relative_to(manifest_dir) usa manifest_dir NAO-resolvido, enquanto a stack e o path sao .resolve()d (linha 383). No runner Windows tempfile devolve nome curto 8.3 (RUNNER~1) e .resolve() expande pro longo (runneradmin) -> relative_to compara textos diferentes e estoura. Fix: usar root (= manifest_dir.resolve(), linha 379) no relative_to da linha 393. Nao reproduz em Windows local sem descasamento curto/longo.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `tests/test_render_includes.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Fix: _expand_includes (render-skills.py:393) usa root (=manifest_dir.resolve()) em vez de manifest_dir cru ao montar o chain do include circular. No runner Windows o tempdir vem em nome curto 8.3 (RUNNER~1) e .resolve() expande pro longo -> relative_to comparava textos diferentes e estourava ValueError em vez de RenderError. Adicionado teste de regressao portatil (test_circular_chain_uses_resolved_manifest_dir) que forca cru!=resolvido via componente '..', reproduzindo o bug em qualquer SO.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- pytest 137 passed (Windows); regressao confirmada (falha com ValueError no codigo antigo, passa com o fix); render --check verde; doctor verde

### Validacao pendente

- Nenhuma.

## [D-071] 🧹 README value-first: o que faz e como usar antes da stack

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-15)
- **Tipo:** Chore
- **Contexto:** Pre-publicacao no GitHub. Aplicar a licao do artigo Akita ('ninguem liga pra sua stack'): o README deve LIDERAR com o que o guia-fluxo faz, o problema que resolve e COMO usar (fluxo + exemplo concreto), e so depois detalhes de stack/arquitetura/instalacao/plugin. Hoje o README mergulha em layout de plugin, marketplace e core/dist antes de mostrar valor. Tambem corrigir handle paulosmarcos -> Paulo-Marcos no README.

### Arquivos modificados/criados

- `FEATURES.md`
- `README.md`
- `dist/.claude-plugin/plugin.json`
- `dist/.claude-plugin/marketplace.json`
- `docs/ROADMAP.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via Guia Fluxo.
- README reescrito value-first: lidera com o que o pack faz, o problema e o fluxo (abre->ready->valida->finish->lock); stack movida pro fim. Handle paulosmarcos->Paulo-Marcos corrigido em plugin.json, marketplace.json, ROADMAP, visao-geral e instalar-em-outro-projeto.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- doctor verde; render --check verde (53 alvos); git grep sem paulosmarcos fora de .guia/FEATURES

### Validacao pendente

- Nenhuma.

## [D-070] 🧹 Docs quick wins: residuo CONTRIBUTING + llms.txt

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-12)
- **Tipo:** Chore
- **Contexto:** Quick wins do mapeamento do artigo Akita (boas praticas OSS na era LLM). (a) Residuo do D-069: CONTRIBUTING.md tabela Tipos em uso ainda lista o verbo issue como atual (linha 78) - trocar para bug via /bug. (b) Avaliar/criar llms.txt minimo na raiz apontando para AGENTS.md, CLAUDE.md, README e docs. Independente de publicar o repo.

### Arquivos modificados/criados

- `FEATURES.md`
- `CONTRIBUTING.md`
- `llms.txt`
- `CHANGELOG.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Em desenvolvimento desde 2026-06-12.
- CONTRIBUTING.md: troquei a linha obsoleta da tabela Tipos em uso (issue -> bug, /issue -> /bug) e atualizei a descricao do chore de [Manutencao sem demanda formal] para [Manutencao entregue via /chore (refactor pequeno, deps, build/lint)], coerente com o modelo atual onde chore E demanda formal D-NNN kind=chore.
- O grep por issue pegou uma 2a referencia VIVA ao verbo removido, no fluxo Abra uma demanda (antiga linha 30): corrigida issue -> bug. Preservei o exemplo historico (issue: Paridade de skills...) e as 3 mencoes legitimas a issue do GitHub (canais de reporte).
- llms.txt CRIADO. Decisao: vale a pena - o repo e uma ferramenta DE agentes, entao um llms.txt minimo e barato e coerente; complementa AGENTS.md (briefing profundo) sem duplicar, e a porta de entrada de 4 linhas. Formato padrao llmstxt.org: H1 + blockquote de 1 linha + bullets para AGENTS.md, CLAUDE.md, README.md, docs/.
- AVISO UNLOCK: llms.txt e arquivo NOVO -> cai no lock global adicoes-exigem-autorizacao (operations add, files asterisco). O commit (feito pelo humano) precisara da marca: [unlock:adicoes-exigem-autorizacao] motivo: adiciona indice llms.txt para agentes.
- Fechada apos validacao humana. CHANGELOG ganhou entradas Added (llms.txt) e Fixed (residuo issue em CONTRIBUTING).

### Validacao feita

- doctor verde (exit 0). Nao toquei core/ nem manifest, render dispensado.

### Validacao pendente

- Nenhuma.

## [D-069] 🧹 Corrigir drift de docs: verbo issue removido

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-11)
- **Tipo:** Chore
- **Contexto:** Pilar 'Documentacao' do artigo Akita. README.md linha 21 ainda lista /guia:issue, removido no ADR-0011 Fase 4 (substituido por /guia:bug). Varrer README.md + docs/ por referencias obsoletas a verbos/IDs removidos (issue, /guia:issue, ai issue, kind=issue usado como verbo) e alinhar ao vocabulario atual (bug, D-NNN). NAO mexer em mencoes legacy intencionais: 'Bug (legacy)', aceitacao de F/I/B-NNN como input, e historico no CHANGELOG/ADR. Independente: edicao de doc pura, sem dependencia de outra frente.

### Arquivos modificados/criados

- `FEATURES.md`
- `README.md`
- `docs/explanation/visao-geral.md`
- `docs/reference/files.md`
- `docs/reference/hooks-git.md`
- `docs/tutorials/primeiro-uso.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/renomear-chat.md`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/how-to/promover-backlog.md`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Em desenvolvimento desde 2026-06-11.
- Removido verbo/atalho obsoleto 'issue' de README e docs vivos: /guia:issue->/guia:bug (README, files.md, instalar-em-outro-projeto, visao-geral), /feature ou /issue->/bug (hooks-git), --kind issue->--kind bug (promover-backlog x2), e ajuste de prosa (files.md 'features e issues'->'features, bugs e chores'; promover-backlog 'feature ou issue'->'feature, bug ou chore'; renomear-chat lista de verbos; manter-docs 'feature/issue'->'demanda'; primeiro-uso 'feature/issue'->'feature/bug/chore').
- Preservadas as mencoes legacy/historicas intencionais: 'Bug (legacy)' e kind=issue navegavel (visao-geral, cli.md), aceitacao de F/I/B-NNN, notas de remocao da Fase 4, ADRs (0004/0006/0010/0011) e auditorias F-014 (snapshots historicos, onde [ISSUE] e rotulo de classificacao, nao o verbo).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- doctor: Guia Fluxo files OK.
- python core/build/render-skills.py --check: OK 53 alvos em sincronia

### Validacao pendente

- Nenhuma.

