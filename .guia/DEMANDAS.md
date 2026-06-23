# Demandas

---

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

- **Status:** Aguardando validacao
- **Origem:** Backlog (2026-06-22)
- **Tipo:** Feature
- **Contexto:** O usuario quer reorganizar a raiz do projeto separando claramente o que e CORE (motor/codigo interno do guia-fluxo) do que e de fato o PLUGIN gerado/exposto para consumo. Percepcao atual: ha arquivos demais expostos na raiz. Objetivo da tarefa: (1) inventariar cada arquivo/pasta exposto na raiz; (2) justificar a razao de existencia/exposicao de cada um; (3) entender os motivos que levaram cada um a estar onde esta; (4) avaliar onde da pra reduzir a superficie exposta, consolidando o que e core num lugar so e deixando exposto apenas o necessario ao plugin. Criterio de sucesso: um mapa raiz->(core|plugin|infra) com justificativa por item e uma proposta de consolidacao que diminua arquivos expostos sem quebrar descoberta do plugin (marketplace.json, .claude-plugin, etc).

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`
- `docs/auditorias/D-094-raiz-core-plugin.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-23.
- Inventario completo da raiz (21 entradas) classificado em CORE/PLUGIN/ESTADO/INFRA-DOCS com justificativa por item; diagnostico de que CORE (core/) e PLUGIN (plugins/) ja estao consolidados e a raiz e quase toda convencao irredutivel; proposta priorizada (P1 VERSION orfao, P2 mover community-health p/ .github/, P3 nao-fazer) respeitando ADR-0017 e a descoberta do plugin.

### Validacao feita

- doctor -> exit 0; render-skills --check -> exit 0 (61 alvos em sincronia)

### Validacao pendente

- Dono decide P1 (remover/dedupe VERSION) e P2 (mover CONTRIBUTING/SECURITY/CODE_OF_CONDUCT p/ .github/) -> viram demandas-filhas; nenhuma movimentacao executada (diagnostico). Bonus: README.md:9 ainda diz v0.1.0 (atual 0.4.0).

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

- **Status:** Em desenvolvimento
- **Origem:** Guia Fluxo (2026-06-22)
- **Tipo:** Feature
- **Contexto:** Filho 1

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`

### O que foi feito

- Demanda criada via Guia Fluxo.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


## [E-001] 🎯 Teste

- **Status:** Em desenvolvimento
- **Origem:** Guia Fluxo (2026-06-22)
- **Tipo:** Epic
- **Contexto:** Teste

### Arquivos modificados/criados

- `.guia/DEMANDAS.md`

### O que foi feito

- Demanda criada via Guia Fluxo.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


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

## [D-068] 🧹 CI roda pytest em matrix Windows+Linux

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-11)
- **Tipo:** Chore
- **Contexto:** Pilar 'Testes + CI' do artigo Akita (boas praticas OSS na era LLM). A suite em tests/ (20+ arquivos) nao roda em nenhum workflow hoje: so render-check (doctor + render --check) e lock-check existem. Adicionar .github/workflows/tests.yml rodando pytest em push + pull_request, matrix ubuntu-latest + windows-latest (e 2 versoes de Python, ex. 3.10 e 3.12). Verificavel localmente: pytest verde + YAML valido. Maior gap / menor esforco do mapeamento. Independente: nao depende de publicar o repo (autoria local self-contained; ativa quando o repo for pro GitHub).

### Arquivos modificados/criados

- `FEATURES.md`
- `.github/workflows/tests.yml`
- `tests/test_tasks_list.py`
- `tests/test_tasks_domain.py`
- `tests/test_features_md.py`
- `tests/test_cli_promote_order.py`
- `tests/test_smoke.py`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Em desenvolvimento desde 2026-06-11.
- Adicionado .github/workflows/tests.yml: pytest em matrix os=[ubuntu-latest,windows-latest] x python=[3.10,3.12], em push(main)+pull_request. Sem pytest.ini (pytest acha tests/ pela raiz). Instala so pyyaml+pytest.
- Escopo expandido (decisao do dev): suite tinha 16 falhas pre-existentes - testes stale vs ADR-0011 (IDs neutros D-NNN + remocao do comando issue). Migrados test_tasks_list/domain/features_md/cli_promote_order/smoke para D-NNN, kind bug, rotulo 'Bug (legacy)', heading com emoji marker e modelo in-place de backlog/promote. Removido test_next_backlog (cobria next_backlog_id, funcao inexistente).
- Fix cross-plataforma: helpers de subprocess dos testes decodificam stdout com encoding=utf-8 (CLI emite emoji via _bootstrap_utf8_io; Windows cp1252 quebrava no marker bug / byte 0x90).
- Docs: entrada no CHANGELOG (Added=workflow CI; Fixed=migracao da suite ao ADR-0011 + fix cp1252/UTF-8).
- Fechado sem commit: tests.yml e arquivo novo sob lock 'adicoes-exigem-autorizacao'; o commit precisa de [unlock:...] que o finish nao injeta.

### Validacao feita

- pytest local verde: 136 passed (Windows)
- render-skills.py --check verde (53 alvos em sincronia)
- doctor verde (Guia Fluxo files OK)
- tests.yml validado com yaml.safe_load (matrix os x python correto)

### Validacao pendente

- Nenhuma.

## [D-059] 🧹 Refactor render-skills: config DI + RenderError

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-10)
- **Tipo:** Chore
- **Contexto:** Refactor de qualidade em core/build/render-skills.py sem mudanca de comportamento externo. P1: trocar estado global mutavel (DIST_DIR/MANIFEST_DIR e derivados) por objeto de config injetado. P2: substituir sys.exit(2) interno por excecao RenderError capturada no main(). P3: centralizar conhecimento de targets num registro unico (fecha OCP). P4: remover codigo morto TARGET_LABELS e BODIES_DIR. P5: extrair handlers por modo do main(). Mais 5 lacunas de teste: guarda do --clean sem flag preserva orfao, marcador ausente do wrapper aborta, reserved frontmatter key aborta, idempotencia de write_outputs, _validate_template_set aborta com template nao declarado. Criterio de sucesso: todos os testes existentes continuam passando + render --check verde.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `tests/test_render_includes.py`
- `tests/test_render_polish.py`
- `tests/test_render_hardening.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via Guia Fluxo.
- P1: estado global mutavel substituido por dataclass Paths (frozen) injetada; load_manifest/collect_outputs/collect_bin_outputs/collect_template_outputs/find_orphans/clean_orphans agora recebem paths
- P2: sys.exit(2) interno trocado por RenderError; main() captura e mapeia para exit 2 (CLI mantem o mesmo contrato de exit code)
- P3: registro TARGETS (TargetSpec) concentra nome/diretorio/host_suffix/label por host; fim dos if target== espalhados
- P4: removidos TARGET_LABELS e BODIES_DIR (codigo morto confirmado por grep)
- P5: main() dividido em _build_arg_parser/_dispatch/_run_check/_run_check_orphans/_run_render + helper _rel
- Testes white-box migrados para a nova API (Paths via dataclasses.replace; RenderError no lugar de SystemExit). Novo tests/test_render_hardening.py cobre 5 lacunas: --clean opt-in, marcador do wrapper, frontmatter reservado, idempotencia, template nao declarado
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python core/build/render-skills.py --check (OK: 53 alvos em sincronia, zero churn no dist/)
- python core/build/render-skills.py --check-orphans (OK: nenhum orfao)
- pytest render suite (51 passed: 42 existentes + 9 novos)

### Validacao pendente

- Nenhuma.

## [D-051] 🧹 Strip legacy mentions and rebalance trigger descriptions

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-08)
- **Tipo:** Chore
- **Contexto:** Two issues raised: (1) Bodies and descriptions reference historical decisions (ADR-0011 Phase 4, F-003, 'replaces old /issue', 'introduced in', 'legacy B-NNN') — this is project history that belongs in commit log + ADRs, not in user-facing skill instructions. Treat this as the initial version of a new tool. (2) Manifest descriptions are unbalanced: heavy on 'Do NOT use for X' routing hints (4-5 alternatives each) and light on what the verb actually does + its options (--context, --origin, --reason, --status, --file, etc.). User wants definition-first, options-listed descriptions with brief disambiguation.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/manifest/bodies/bug.md`
- `core/manifest/bodies/chore.md`
- `core/manifest/bodies/ready.md`
- `core/manifest/bodies/plan.md`
- `core/manifest/bodies/backlog.md`
- `core/manifest/manifest.yaml`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `dist/.agents/skills/guia-backlog/SKILL.md`
- `dist/.agents/skills/guia-block/SKILL.md`
- `dist/.agents/skills/guia-bug/SKILL.md`
- `dist/.agents/skills/guia-cancel/SKILL.md`
- `dist/.agents/skills/guia-chore/SKILL.md`
- `dist/.agents/skills/guia-feature/SKILL.md`
- `dist/.agents/skills/guia-finish/SKILL.md`
- `dist/.agents/skills/guia-fluxo/SKILL.md`
- `dist/.agents/skills/guia-plan/SKILL.md`
- `dist/.agents/skills/guia-promote/SKILL.md`
- `dist/.agents/skills/guia-ready/SKILL.md`
- `dist/.agents/skills/guia-start/SKILL.md`
- `dist/.agents/skills/guia-status/SKILL.md`
- `dist/.agents/skills/guia-unblock/SKILL.md`
- `dist/skills/backlog/SKILL.md`
- `dist/skills/block/SKILL.md`
- `dist/skills/bug/SKILL.md`
- `dist/skills/cancel/SKILL.md`
- `dist/skills/chore/SKILL.md`
- `dist/skills/feature/SKILL.md`
- `dist/skills/finish/SKILL.md`
- `dist/skills/guia-fluxo/SKILL.md`
- `dist/skills/plan/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `dist/skills/ready/SKILL.md`
- `dist/skills/start/SKILL.md`
- `dist/skills/status/SKILL.md`
- `dist/skills/unblock/SKILL.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Stripped historical/legacy references from 5 bodies. bug.md: removed 'Replaces the old /issue (removed in ADR-0011 Phase 4 ...)'. chore.md: removed 'Introduced in ADR-0011 Phase 4.'. ready.md: removed '(the reason validate was deprecated in F-003)'. plan.md: 'legacy B-NNN' -> 'backlog item'. backlog.md: removed '(new D-NNN + legacy B-NNN)' qualifier.
- Rewrote all 14 manifest descriptions. New convention (documented in manifest.yaml header): (1) canonical ADR-0010 prefix, (2) short definition, (3) real CLI options/flags, (4) brief disambiguation (1-2 alternatives, not 4-5), (5) no historical mentions. All EN for consistency. Each description now lists the actual flags an agent can pass (--context, --origin, --status, --reason, --file, --summary, --validation, --pending, --docs-touched, --docs-skip, --no-commit, --lock, --keep-worktree, --set-current, --note, --kind, --assessment, --plan, --worktree, etc.) instead of just enumerating verbs to NOT use.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python core/build/render-skills.py --check (53 targets in sync)
- python core/build/render-skills.py --check-orphans (zero orphans)
- grep for ADR-0011|Phase 4|legacy|Replaces the old|substitui o antigo|Introduced in|deprecated|removed in in dist/skills/ and dist/.agents/skills/ returns no files - zero legacy mentions in user-facing skill content
- Spot-checked dist/skills/bug/SKILL.md - description shows new definition-first form, body intro shows clean 'Use for a regression, a defect, or any incorrect behavior' without ADR references
- render+manifest+include+partial tests: 42/42 pass
- Full suite: 128 tests, same 14 pre-existing failures + 2 pre-existing errors unchanged (zero regression)

### Validacao pendente

- Nenhuma.

## [D-050] 🧹 Consolidate per-verb bodies via host-aware include

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-08)
- **Tipo:** Chore
- **Contexto:** After D-047, the only truly host-specific bit in each verb body is the post_cli include (codex_app vs mark_chapter). Everything else (intro text, command examples, flag explanations, fallback line) is gratuitous textual variation between *.agent.md and *.claude.md. Introduce {{include_per_target: <path-without-host-suffix>}} directive in the renderer that resolves to <path>.agent.md or <path>.claude.md based on which target is being generated. Consolidate 28 per-host body files (14 verbs x 2 targets) into 14 single bodies plus the existing 4 partials. dist/ output must stay equivalent.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/feature.md`
- `core/manifest/bodies/bug.md`
- `core/manifest/bodies/chore.md`
- `core/manifest/bodies/backlog.md`
- `core/manifest/bodies/promote.md`
- `core/manifest/bodies/ready.md`
- `core/manifest/bodies/finish.md`
- `core/manifest/bodies/status.md`
- `core/manifest/bodies/cancel.md`
- `core/manifest/bodies/block.md`
- `core/manifest/bodies/unblock.md`
- `core/manifest/bodies/plan.md`
- `core/manifest/bodies/start.md`
- `core/manifest/bodies/guia-fluxo.md`
- `tests/test_render_includes.py`
- `tests/test_manifest_layout_b.py`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `dist/.agents/skills/guia-backlog/SKILL.md`
- `dist/.agents/skills/guia-block/SKILL.md`
- `dist/.agents/skills/guia-bug/SKILL.md`
- `dist/.agents/skills/guia-cancel/SKILL.md`
- `dist/.agents/skills/guia-chore/SKILL.md`
- `dist/.agents/skills/guia-feature/SKILL.md`
- `dist/.agents/skills/guia-finish/SKILL.md`
- `dist/.agents/skills/guia-fluxo/SKILL.md`
- `dist/.agents/skills/guia-plan/SKILL.md`
- `dist/.agents/skills/guia-promote/SKILL.md`
- `dist/.agents/skills/guia-ready/SKILL.md`
- `dist/.agents/skills/guia-start/SKILL.md`
- `dist/.agents/skills/guia-status/SKILL.md`
- `dist/.agents/skills/guia-unblock/SKILL.md`
- `dist/skills/backlog/SKILL.md`
- `dist/skills/block/SKILL.md`
- `dist/skills/bug/SKILL.md`
- `dist/skills/cancel/SKILL.md`
- `dist/skills/chore/SKILL.md`
- `dist/skills/feature/SKILL.md`
- `dist/skills/finish/SKILL.md`
- `dist/skills/guia-fluxo/SKILL.md`
- `dist/skills/plan/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `dist/skills/ready/SKILL.md`
- `dist/skills/start/SKILL.md`
- `dist/skills/status/SKILL.md`
- `dist/skills/unblock/SKILL.md`
- `docs/adr/0013-consolidacao-bodies-por-verbo.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Phase 1: added {{include_per_target: <base>}} directive to render-skills.py. Pre-processed BEFORE the regular {{include:}} expansion - substitutes the directive with {{include: <base>.<host>.md}} based on which target (agent_skill or claude_skill) is being rendered. Aborts if a body uses the directive but the target_name has no mapping in TARGET_HOST_SUFFIX.
- Phase 2: audited all 14 verbs (feature/bug/chore/backlog/promote/ready/finish/status/cancel/block/unblock/plan/start/guia-fluxo). Confirmed the only truly host-specific bit in 13 of them is the rename mechanism (already in post_cli.<host>.md). For guia-fluxo, kept the host differences readable inline (Codex /feature vs Claude /guia:feature, Tool Notes per host section) since it is a reference doc - readers benefit from seeing the full host picture.
- Phase 3: created 14 consolidated bodies/<verb>.md replacing 28 *.agent.md + *.claude.md pairs. Lifecycle verbs (status/cancel/block/unblock/plan/start) were also migrated to partials (they had not been in D-047). Updated manifest.yaml so both targets of each verb point body_file to the consolidated file (preserves test_every_target_has_body_file). Total bodies/: from 32 files (28 per-host + 4 partials + README) down to 19 (14 consolidated + 4 partials + README).
- Phase 4: rewrote test_manifest_layout_b.SharedBodyCacheTests to assert (a) every verb has agent_skill.body_file == claude_skill.body_file in the manifest, and (b) the dist outputs of feature differ only in the host-aware section (codex_app in agent target, mark_chapter in claude target). Deleted the 28 legacy per-host body files.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python core/build/render-skills.py --check (53 targets in sync)
- python core/build/render-skills.py --check-orphans (zero orphans)
- render+manifest+include+partial test suite: 42/42 pass
- Full suite: 128 tests (vs 123 before), 14 pre-existing failures + 2 pre-existing errors unchanged (zero regression from D-050)
- Spot-checked dist/skills/block/SKILL.md - composition uses post_cli.claude.md (mark_chapter) and no {{include literal survives
- Cross-contamination check: grep for mark_chapter in agent skills returns empty; grep for codex_app in claude skills returns empty

### Validacao pendente

- Nenhuma.

## [D-047] ✨ Add partial includes to skill bodies

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-08)
- **Tipo:** Feature
- **Contexto:** Introduce a {{include: ...}} directive in render-skills.py so each shim body can pull shared post-CLI playbooks from core/manifest/bodies/_partials/. Migrate the 7 verb shims (feature/bug/chore/backlog/promote/ready/finish) to use the partials, add mark_chapter as a reliable rename surrogate for Claude Code, and simplify guia-fluxo into pure reference once all behavior lives in partials. Goal: kill duplication between *.agent.md and *.claude.md while keeping host-specific differences.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `core/manifest/bodies/_partials/README.md`
- `core/manifest/bodies/_partials/title_context_rules.md`
- `core/manifest/bodies/_partials/lock_protocol.md`
- `core/manifest/bodies/_partials/post_cli.agent.md`
- `core/manifest/bodies/_partials/post_cli.claude.md`
- `core/manifest/bodies/feature.agent.md`
- `core/manifest/bodies/feature.claude.md`
- `core/manifest/bodies/bug.agent.md`
- `core/manifest/bodies/bug.claude.md`
- `core/manifest/bodies/chore.agent.md`
- `core/manifest/bodies/chore.claude.md`
- `core/manifest/bodies/backlog.agent.md`
- `core/manifest/bodies/backlog.claude.md`
- `core/manifest/bodies/promote.agent.md`
- `core/manifest/bodies/promote.claude.md`
- `core/manifest/bodies/ready.agent.md`
- `core/manifest/bodies/ready.claude.md`
- `core/manifest/bodies/finish.agent.md`
- `core/manifest/bodies/finish.claude.md`
- `core/manifest/bodies/guia-fluxo.agent.md`
- `core/manifest/bodies/guia-fluxo.claude.md`
- `tests/test_render_includes.py`
- `tests/test_body_partials.py`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `dist/.agents/skills/guia-backlog/SKILL.md`
- `dist/.agents/skills/guia-bug/SKILL.md`
- `dist/.agents/skills/guia-chore/SKILL.md`
- `dist/.agents/skills/guia-feature/SKILL.md`
- `dist/.agents/skills/guia-finish/SKILL.md`
- `dist/.agents/skills/guia-fluxo/SKILL.md`
- `dist/.agents/skills/guia-promote/SKILL.md`
- `dist/.agents/skills/guia-ready/SKILL.md`
- `dist/skills/backlog/SKILL.md`
- `dist/skills/bug/SKILL.md`
- `dist/skills/chore/SKILL.md`
- `dist/skills/feature/SKILL.md`
- `dist/skills/finish/SKILL.md`
- `dist/skills/guia-fluxo/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `dist/skills/ready/SKILL.md`
- `docs/adr/0012-partials-em-bodies.md`

### O que foi feito

- Demanda criada via Guia Fluxo.
- Phase 1: extended render-skills.py with {{include:}} directive (recursive, with path-traversal and circular-include guards; paths resolve relative to the including file's directory).
- Phase 2: created 4 shared partials in core/manifest/bodies/_partials/: title_context_rules.md, lock_protocol.md (host-agnostic), post_cli.agent.md and post_cli.claude.md (host-specific).
- Phase 3: migrated 14 verb shims (feature/bug/chore/backlog/promote/ready/finish, agent+claude) to compose the partials via {{include:}}. Each shim now carries only its verb-specific intro + the CLI command; shared protocol lives in the partials.
- Phase 4: simplified guia-fluxo.{agent,claude}.md. The 'Agent Behavior' list (13 items) was removed because every item now has a home: items 2-7 in post_cli partial, item 8 in lock_protocol partial, items 9-13 in the respective verb shims. guia-fluxo is now pure reference (Trigger Commands + Core Rule + Tool Notes + Portability + new 'Where Behavior Lives' index pointing to partials).
- Added mark_chapter (mcp__ccd_session__mark_chapter) as the reliable rename surrogate in post_cli.claude.md, complementing /rename when the build supports it.
- Phase 5: added tests/test_render_includes.py (9 tests covering the {{include:}} mechanism: basic expansion, inline-prose left alone, relative-to-including-file path resolution, recursive partial-includes-partial, missing-file abort, path-traversal block, circular-include detection, no-unexpanded-include in dist/) and tests/test_body_partials.py (13 tests covering actual composition: partials directory and README exist, expected 4 partials present, title_context appears only in create-verbs and not in lifecycle-verbs, lock_protocol appears only in editing-verbs and not in ready/backlog, post_cli appears in all 7 shims, mark_chapter appears only in claude targets and codex_app only in agent targets with no cross-contamination, frontmatter name/description correctness).
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- python core/build/render-skills.py --check (53 targets in sync)
- python core/build/render-skills.py --check-orphans (zero orphans)
- python core/src/guia.py doctor (Guia Fluxo files OK)
- Spot-checked dist/skills/feature/SKILL.md and dist/.agents/skills/guia-ready/SKILL.md - partials expand inline cleanly
- 22/22 new tests pass
- Baseline render+manifest tests (15) still pass - zero regression
- Full suite: 123 tests (101 baseline + 22 new), same 14 pre-existing failures + 2 pre-existing errors (unrelated to D-047 - they touch state JSON / smoke / promote-order)

### Validacao pendente

- Nenhuma.

## [D-046] ✨ Rename guia-fluxo -> Guia Fluxo (slug: guia). Escopo total sem compat: renomear shims /guia:* -> /guia:*, namespace plugin ai -> guia, binario guia.ps1 -> guia.ps1, diretorio .guia/ -> .guia/, package guia-fluxo -> guia-fluxo, todas referencias em docs/ADRs/scripts/CLAUDE.md/AGENTS.md. Pasta raiz do repo tambem sera renomeada no final (manual, com Claude fechado). Sem aliases de transicao. Decisoes confirmadas pelo usuario em chat.

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Rename guia-fluxo -> Guia Fluxo (slug: guia). Escopo total sem compat: renomear shims /guia:* -> /guia:*, namespace plugin ai -> guia, binario guia.ps1 -> guia.ps1, diretorio .guia/ -> .guia/, package guia-fluxo -> guia-fluxo, todas referencias em docs/ADRs/scripts/CLAUDE.md/AGENTS.md. Pasta raiz do repo tambem sera renomeada no final (manual, com Claude fechado). Sem aliases de transicao. Decisoes confirmadas pelo usuario em chat.

### Arquivos modificados/criados

- `FEATURES.md`
- `.claude/settings.json`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/render-check.yml`
- `.gitignore`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/docs-map.yaml`
- `.guia/process.json`
- `.guia/tasks.json`
- `AGENTS.md`
- `CHANGELOG.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `README.md`
- `SECURITY.md`
- `core/bin/guia`
- `core/bin/guia.ps1`
- `core/build/render-skills.py`
- `core/lock/lock_api.py`
- `core/manifest/bodies/backlog.agent.md`
- `core/manifest/bodies/backlog.claude.md`
- `core/manifest/bodies/block.agent.md`
- `core/manifest/bodies/block.claude.md`
- `core/manifest/bodies/bug.agent.md`
- `core/manifest/bodies/bug.claude.md`
- `core/manifest/bodies/cancel.agent.md`
- `core/manifest/bodies/cancel.claude.md`
- `core/manifest/bodies/chore.agent.md`
- `core/manifest/bodies/chore.claude.md`
- `core/manifest/bodies/feature.agent.md`
- `core/manifest/bodies/feature.claude.md`
- `core/manifest/bodies/finish.agent.md`
- `core/manifest/bodies/finish.claude.md`
- `core/manifest/bodies/guia-fluxo.agent.md`
- `core/manifest/bodies/guia-fluxo.claude.md`
- `core/manifest/bodies/plan.agent.md`
- `core/manifest/bodies/plan.claude.md`
- `core/manifest/bodies/promote.agent.md`
- `core/manifest/bodies/promote.claude.md`
- `core/manifest/bodies/ready.agent.md`
- `core/manifest/bodies/ready.claude.md`
- `core/manifest/bodies/start.agent.md`
- `core/manifest/bodies/start.claude.md`
- `core/manifest/bodies/status.agent.md`
- `core/manifest/bodies/status.claude.md`
- `core/manifest/bodies/unblock.agent.md`
- `core/manifest/bodies/unblock.claude.md`
- `core/manifest/manifest.yaml`
- `core/src/_cli_creation.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_tasks.py`
- `core/src/_constants.py`
- `core/src/_docs_hook.py`
- `core/src/_features_md.py`
- `core/src/_process_config.py`
- `core/src/_reports.py`
- `core/src/_tasks.py`
- `core/src/guia.py`
- `dist/.claude-plugin/marketplace.json`
- `dist/.claude-plugin/plugin.json`
- `dist/bin/_cli_creation.py`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/_cli_tasks.py`
- `dist/bin/_constants.py`
- `dist/bin/_docs_hook.py`
- `dist/bin/_features_md.py`
- `dist/bin/_process_config.py`
- `dist/bin/_reports.py`
- `dist/bin/_tasks.py`
- `dist/bin/lock_api.py`
- `dist/skills/backlog/SKILL.md`
- `dist/skills/block/SKILL.md`
- `dist/skills/bug/SKILL.md`
- `dist/skills/cancel/SKILL.md`
- `dist/skills/chore/SKILL.md`
- `dist/skills/feature/SKILL.md`
- `dist/skills/finish/SKILL.md`
- `dist/skills/plan/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `dist/skills/ready/SKILL.md`
- `dist/skills/start/SKILL.md`
- `dist/skills/status/SKILL.md`
- `dist/skills/unblock/SKILL.md`
- `docs/README.md`
- `docs/ROADMAP.md`
- `docs/adr/0001-script-fonte-da-verdade.md`
- `docs/adr/0003-json-maquina-markdown-humano.md`
- `docs/adr/0004-chat-title-sincronizado.md`
- `docs/adr/0005-docs-hook-no-finish.md`
- `docs/adr/0006-plugin-oficial-claude-code.md`
- `docs/adr/0007-arquitetura-modular-core-src.md`
- `docs/adr/0008-layout-b-manifest.md`
- `docs/adr/0009-yaml-para-manifest.md`
- `docs/adr/0010-prefixos-trigger-skill-descriptions.md`
- `docs/adr/0011-modelo-de-demanda-tipo-x-status.md`
- `docs/adr/README.md`
- `docs/auditorias/F-014-core.md`
- `docs/auditorias/F-014-validacao.md`
- `docs/explanation/por-que-docs-hook.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/how-to/promover-backlog.md`
- `docs/reference/cli.md`
- `docs/reference/docs-map.md`
- `docs/reference/files.md`
- `docs/reference/troubleshooting.md`
- `docs/tutorials/primeiro-uso.md`
- `install.ps1`
- `install.sh`
- `tests/test_cli_promote_order.py`
- `tests/test_constants.py`
- `tests/test_doctor_extended.py`
- `tests/test_features_md.py`
- `tests/test_install.py`
- `tests/test_manifest_layout_b.py`
- `tests/test_render_polish.py`
- `tests/test_smoke.py`
- `tests/test_tasks_list.py`

### O que foi feito

- Demanda criada via guia-fluxo.
- Demanda finalizada via Guia Fluxo.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-045] 🧹 ADR-0011 Fase 5: docs + ADR-0011 -> Aceita

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Chore
- **Contexto:** Quinta e ultima fase da onda ADR-0011 + B-017. Atualizar todos os docs Diataxis para refletir o novo modelo (kind plural feature/bug/chore, status Backlog/Planejada/Em desenvolvimento, ID neutro D-NNN, emojis ✨🐛🧹, verbos plan/start/cancel/block/unblock/backlog migrate). Mover ADR-0011 de Proposta para Aceita com secao 'Como foi implementado'. Addendum ao ADR-0010 documentando os novos prefixos canonicos. Entrada no CHANGELOG cobrindo as 5 fases. ROADMAP marca onda como entregue. CLAUDE.md/AGENTS.md/cli.md/visao-geral.md sincronizados.

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/adr/0011-modelo-de-demanda-tipo-x-status.md`
- `docs/adr/0010-prefixos-trigger-skill-descriptions.md`
- `docs/adr/README.md`
- `docs/explanation/visao-geral.md`
- `docs/reference/cli.md`
- `CLAUDE.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/ROADMAP.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Fase 5 (ultima) do ADR-0011 entregue. ADR-0011 movido de Proposta para Aceita com secao 'Como foi implementado' listando as 6 tasks de entrega (F-030, D-033, D-035, D-039, D-042, D-045) e as 3 decisoes operacionais (D1/D2/D3). Indice em docs/adr/README.md atualizado. ADR-0010 ganhou addendum: tabela agora tem 12 prefixos canonicos (5 novos: TERMINAL CANCEL, PAUSE in-flight task, RESUME a paused task, PLAN, START) + nota explicando que PRIMARY TRIGGER cobre feature/bug/chore (issue removido). visao-geral.md: secao 'Modelo de demanda' nova com diagrama de ciclo de vida + fluxo recomendado atualizado (verbos novos, --status, kind plural, emojis). cli.md: sessoes bug/chore/plan/start/backlog migrate adicionadas; sessao issue REMOVIDA; tabela de aliases atualizada (13 linhas + coluna emoji) com aviso de removal. CLAUDE.md: tabela de atalhos ganhou /guia:bug, /guia:chore, /guia:plan, /guia:start + coluna emoji; perdeu /guia:issue. AGENTS.md: regra 2 menciona bug/chore; fluxo padrao lista os 4 verbos criadores com snippet --status; convencoes de commit atualizadas; secao 'Quando o pedido nao se encaixa' usa /bug em vez de /issue. CHANGELOG.md: entrada na [Unreleased] resumindo a onda toda (Added + Changed). ROADMAP.md: secao Entregue ganha linha da onda.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; render --check OK (53 alvos em sincronia). Docs cruzados manualmente entre si para coerencia (D-045 sendo a task que escreve sobre as outras, foi necessario validar referencias).

### Validacao pendente

- Nenhuma.

## [D-044] 🧹 SMOKE: testar verbo chore

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Chore
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke fase 4 - validou verbo chore + emoji 🧹

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-043] 🐛 SMOKE: testar verbo bug

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Bug / regressao
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke fase 4 - validou verbo bug + emoji 🐛

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-042] ✨ ADR-0011 Fase 4: substituir issue por bug + adicionar chore

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Quarta fase do ADR-0011 (D2 confirmado pelo usuario): remocao limpa de issue como verbo/skill. ai issue + /guia:issue removidos. Adicionar ai bug + /guia:bug + ai chore + /guia:chore como novos cidadaos de primeira classe. KIND_ISSUE permanece como legacy-read em _constants (preserva renderizacao de I-006/I-007 antigas e D-NNN ja criadas com kind=issue). Atualiza promote --kind e backlog promote --kind para {feature, bug, chore} (issue some). tasks filter --kind aceita {feature, bug, chore, issue} para permitir filtrar legacy. _docs_hook.py: kind_label generico. Render --clean apaga dist/skills/issue + dist/.agents/skills/guia-issue.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/guia.py`
- `core/src/_docs_hook.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/bug.claude.md`
- `core/manifest/bodies/bug.agent.md`
- `core/manifest/bodies/chore.claude.md`
- `core/manifest/bodies/chore.agent.md`
- `core/manifest/bodies/issue.claude.md`
- `core/manifest/bodies/issue.agent.md`
- `dist/skills/bug/SKILL.md`
- `dist/.agents/skills/guia-bug/SKILL.md`
- `dist/skills/chore/SKILL.md`
- `dist/.agents/skills/guia-chore/SKILL.md`
- `dist/skills/issue/SKILL.md`
- `dist/.agents/skills/guia-issue/SKILL.md`
- `dist/bin/_docs_hook.py`
- `dist/bin/guia.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Fase 4 do ADR-0011 (D2 confirmado): troca limpa de issue por bug + adicao de chore. Subcomando ai issue removido (argparse rejeita 'issue' como choice valida); skill /guia:issue removida; bodies/issue.{claude,agent}.md deletados; dist/skills/issue + dist/.agents/skills/guia-issue removidos via render --clean. Novos cidadaos de primeira classe: ai bug + /guia:bug (kind=bug, emoji 🐛) e ai chore + /guia:chore (kind=chore, emoji 🧹), ambos compartilhando _add_task_args (--status backlog|planned|in-development). promote --kind e backlog promote --kind passam a aceitar feature|bug|chore (issue some). tasks filter --kind aceita feature|bug|chore|issue (issue mantido como filtro legacy para tasks antigas). _docs_hook.kind_label usa task.get('kind') generico em vez de comparacao binaria feature/issue. KIND_ISSUE preservado em _constants para legacy-read (KIND_LABELS mapeia para 'Bug (legacy)', KIND_MARKERS mapeia para 🐛). I-006/I-007 antigas continuam renderizando.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; render --clean OK (53 alvos; +4 bug/chore skills, -2 issue skills); render --check em sincronia. Smoke: ai bug 'X' -> D-043 com chat-title '🐛 - #DEV'; ai chore 'Y' -> D-044 com chat-title '🧹 - #DEV'; ai issue 'Z' -> erro argparse 'invalid choice: issue' (subcomando removido com sucesso). Smokes cancelados. tasks list renderiza 🐛/🧹/✨/• corretamente.

### Validacao pendente

- Nenhuma.

## [D-041] ✨ SMOKE start-from-backlog

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-07)
- **Tipo:** Feature
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Em desenvolvimento desde 2026-06-07: atalho direto do backlog.
- Cancelada em 2026-06-07: smoke fase 3 - validou backlog->start atalho + double-start guard

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-040] ✨ SMOKE plan/start - test1

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Em desenvolvimento desde 2026-06-07: smoke kick-off.
- Planejada em 2026-06-07: smoke replanning.
- Em desenvolvimento desde 2026-06-07.
- Cancelada em 2026-06-07: smoke fase 3 - validou --status planned + plan/start cycle

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-039] ✨ ADR-0011 Fase 3 + B-017: status Planejada com verbos plan/start

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Terceira fase do ADR-0011 (implementa B-017). Adicionar verbos plan <id> (transita Backlog/Em desenvolvimento -> Planejada) e start <id> (transita Backlog/Planejada -> Em desenvolvimento). Adicionar flag --status backlog|planned|in-development em i feature e i issue (default in-development). Adicionar 2 novos verbos no manifest (plan/start) com bodies + dist outputs. Skills: /guia:plan, /guia:start. Tasks que saem de Backlog passam a aparecer em FEATURES.md (entram no catalogo). Smoke tests cobrem todas as transicoes validas + as guardas (transicao terminal proibida).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_creation.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/plan.claude.md`
- `core/manifest/bodies/plan.agent.md`
- `core/manifest/bodies/start.claude.md`
- `core/manifest/bodies/start.agent.md`
- `dist/skills/plan/SKILL.md`
- `dist/.agents/skills/guia-plan/SKILL.md`
- `dist/skills/start/SKILL.md`
- `dist/.agents/skills/guia-start/SKILL.md`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/_cli_creation.py`
- `dist/bin/guia.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Fase 3 do ADR-0011 (que implementa B-017) entregue. _cli_lifecycle: cmd_plan transita Backlog/Em desenvolvimento -> Planejada com guarda contra estados terminais e Aguardando validacao; cmd_start transita Backlog/Planejada -> Em desenvolvimento com guarda equivalente. Helper _attach_features_md inclui FEATURES.md em modifiedFiles quando a task sai do backlog (idempotente). _cli_creation.cmd_create_task: aceita args.status via novo _STATUS_FROM_CLI map; quando status=Backlog, pula upsert (consistente com cmd_backlog_add); demais status entram no catalogo. guia.py: parsers plan e start com --note opcional; _add_task_args ganha --status backlog|planned|in-development (default in-development), compartilhado entre feature e issue. Manifest: 2 novos verbos plan e start com prefixos novos PLAN e START + bodies bodies/{plan,start}.{claude,agent}.md. Render gerou 7 alvos novos.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; render OK (51 alvos totais; +4 de plan/start, +3 de dist/bin). Smoke completo: ai feature 'X' --status planned -> D-040 status=Planejada com #PLANEJADA no chat-title; ai start D-040 --note 'kick-off' -> #DEV; ai plan D-040 --note 'replanning' -> #PLANEJADA; ai start D-040 -> #DEV (ciclo idempotente). ai backlog add 'Y' -> D-041 Backlog; ai start D-041 -> #DEV (atalho direto, sem precisar de plan). ai start D-041 segunda vez -> erro 'ja Em desenvolvimento' (guarda). FEATURES.md absorveu D-040 e D-041 ao saírem de Backlog/Planejada. Smokes cancelados.

### Validacao pendente

- Nenhuma.

## [D-038] ✨ SMOKE: marker backlog default kind

- **Status:** Cancelada
- **Origem:** Backlog (2026-06-07)
- **Tipo:** Feature
- **Contexto:** x

### Arquivos modificados/criados

- Nenhuma.

### O que foi feito

- Cancelada em 2026-06-07: smoke test markers - validou backlog default kind=feature emoji ✨

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.


## [D-037] 🐛 SMOKE: marker issue (legacy)

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Bug (legacy)
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke test markers - validou kind=issue (legacy) emoji 🐛

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-036] ✨ SMOKE: marker feature

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** x

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke test markers - validou kind=feature emoji ✨

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-035] ✨ Marcadores visuais de kind (emoji) nas demandas D-NNN

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Resposta ao feedback do usuario na sessao do ADR-0011 Fase 2: 'Eu queria que tivesse a implementacao de Feature e Bug. Pq acho que ficaria mais claro ao ver a demanda do que se trata. So D e muito generico.' Decisao: manter ID neutro D-NNN (preserva principio do ADR-0011 - renomear tipo nao muda ID) e ganhar diferenciacao visual via emoji por kind. Aplicar em todas as superficies de display: chat-title, tasks list, backlog list, FEATURES.md heading. KIND_MARKERS: feature=✨, bug=🐛, chore=🧹, issue=🐛 (legacy).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_tasks.py`
- `core/src/_features_md.py`
- `core/src/_cli_creation.py`
- `core/src/guia.py`
- `.guia/process.json`
- `dist/bin/_constants.py`
- `dist/bin/_tasks.py`
- `dist/bin/_features_md.py`
- `dist/bin/_cli_creation.py`
- `dist/bin/guia.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Marcadores visuais de kind (emoji) introduzidos em todas as superficies de display. _constants.py: KIND_MARKERS={feature:✨, bug:🐛, chore:🧹, issue:🐛 (legacy)} + KIND_MARKER_FALLBACK='•' (legacy backlog items sem kind). CHAT_TITLE_FORMAT_DEFAULT atualizado para '{id} {kindMarker} - #{statusTag} - {title}'. _tasks.py: helper kind_marker(kind) que resolve via KIND_MARKERS com fallback; chat_title injeta kindMarker no template.format; format_task_line ('tasks list') inclui marker entre id e status. _features_md.py: render_features_block adiciona marker antes do title no heading H2 - tasks criadas/atualizadas apos esta fase renderizam '## [D-NNN] ✨ Title'. _cli_creation.py: cmd_backlog_list mostra marker para entradas em tasks.json e para items legacy de backlog.json (fallback '•' nos legacy sem kind). guia.py: novo _bootstrap_utf8_io() forca stdout/stderr para UTF-8 - sem isso, console Windows cp1252 quebrava em UnicodeEncodeError ao imprimir ✨ (\\u2728). .guia/process.json atualizado para o novo CHAT_TITLE_FORMAT (config local; default_process ja apontava para o novo via CHAT_TITLE_FORMAT_DEFAULT, mas process.json existente nao se atualiza sozinho).
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; render OK (5 alvos dist/bin sincronizados). Smoke manual: ai feature 'X' -> D-036 chat-title '✨ - #DEV'; ai issue 'Y' -> D-037 chat-title '🐛 - #DEV'; ai backlog add 'Z' -> D-038 chat-title '✨ - #BACKLOG'; ai backlog list -> D-038 ✨ + B-019/B-018/... com fallback '•'; ai tasks list -> mistura de ✨/🐛/• corretos; FEATURES.md headings de D-036/D-037 com emoji embutido (D-035 ainda sem - ganhara no finish desta task). Todos os smokes (D-036, D-037, D-038) cancelados.

### Validacao pendente

- Nenhuma.

## [D-034] SMOKE: promote D-NNN backlog preserva ID

- **Status:** Cancelada
- **Origem:** Backlog D-034 promovido (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Smoke test promote nova fonte.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Backlog D-034 promovido via guia-fluxo.
- Avaliacao IA: Confirma promote in-place.
- Cancelada em 2026-06-07: smoke test fase 2 - validou backlog add (D-NNN status=Backlog), backlog list (union tasks+legacy), promote in-place preservando ID, migrate --dry-run

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-033] ADR-0011 Fase 2: backlog absorvido em tasks.json (status=Backlog)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Segunda fase do ADR-0011. backlog.json deixa de ser source-of-truth: novas entradas viram task em tasks.json com kind=feature (default) e status=Backlog. backlog.json legacy (B-NNN existentes) permanece read-only e e lido como uniao em 'ai backlog list' e 'ai promote'. Adicionar 'ai backlog migrate' (com --dry-run e --force) para copiar B-NNN antigos para tasks.json preservando id. FEATURES.md NAO recebe entradas com status=Backlog - mantem-se como catalogo de tasks 'em curso' ou validadas. cmd_promote aceita id de qualquer fonte (tasks.json com status=Backlog OU backlog.json legacy).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_creation.py`
- `core/src/_tasks.py`
- `core/src/guia.py`
- `dist/bin/_cli_creation.py`
- `dist/bin/_tasks.py`
- `dist/bin/guia.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Fase 2 do ADR-0011 implementada. _tasks.new_task agora aceita 'status' opcional (default STATUS_IN_DEVELOPMENT); quando status=Backlog, omite modifiedFiles, summary e pending defaults (nao houve implementacao ainda). _tasks.next_backlog_id removido (PREFIX_BACKLOG nao gera mais IDs novos). _cli_creation.cmd_backlog_add: cria task em tasks.json com kind=feature + status=Backlog + ID D-NNN; nao escreve em backlog.json; nao chama upsert_features_entry (backlog fica fora do catalogo FEATURES.md). _cli_creation.cmd_backlog_list: une fontes - mostra tasks com status=Backlog em tasks.json primeiro + itens legacy de backlog.json em seguida. _cli_creation.cmd_promote: nova logica de dois caminhos via _find_backlog_source - se id existe em tasks.json (status=Backlog), promove in-place preservando ID (status -> Em desenvolvimento, kind atualizado); se id existe em backlog.json (B-NNN legacy), cria nova D-NNN com backlogId apontando para o legacy e remove o item antigo (caminho atual mantido). Novo cmd_backlog_migrate: dry-run por default, --force aplica copia preservando ID original; idempotente (skip se id ja em tasks.json); esvazia backlog.json apos migracao com sucesso. Parser 'backlog migrate' registrado em guia.py.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; render OK (47 alvos, 3 .py em dist/bin sincronizados). Smoke tests: backlog add 'X' -> D-034 (status=Backlog em tasks.json, nao em backlog.json); backlog list -> mostra D-034 + B-019,B-018,...,B-002 (uniao); promote D-034 --kind feature -> D-034 mantem ID, status=Em desenvolvimento, origin='Backlog D-034 promovido'; backlog migrate --dry-run -> lista 9 B-NNN legacy candidatos sem escrever. D-034 cancelada ao final.

### Validacao pendente

- Nenhuma.

## [D-032] SMOKE: validar issue ainda gera D-NNN com kind=issue

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Bug (legacy)
- **Contexto:** Descartavel - confirmar que ai issue continua funcional (Fase 4 removera) e gera D-NNN com kind=issue.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke test fase 1 - validou ai issue ainda funcional + D-NNN gerado para qualquer kind

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [D-031] SMOKE: validar geracao D-NNN

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Descartavel - confirmar prefixo D-NNN, kind=feature, status=Em desenvolvimento.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Cancelada em 2026-06-07: smoke test fase 1 - validou geracao D-NNN

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [F-030] ADR-0011 Fase 1: ID neutro D-NNN + kind plural (bug/chore) + leitura multi-prefixo

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-07)
- **Tipo:** Feature
- **Contexto:** Primeira fase da implementacao do ADR-0011 (F-024) e do plano de B-017. Escopo focado: introduzir prefixo D-NNN como gerador unico de IDs (numeracao monotonica considerando max(D,F,I)+1), adicionar constantes KIND_BUG e KIND_CHORE + STATUS_BACKLOG, ampliar KIND_LABELS preservando KIND_ISSUE como legacy-read, atualizar TASK_HEADING_RE e o regex inline em _features_md para aceitar [DFI]. Sem mudancas em manifest/skills/docs nesta fase. Sem remocao de issue (Fase 4 cuida). Sem absorcao de backlog (Fase 2 cuida).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_tasks.py`
- `core/src/_features_md.py`
- `dist/bin/_constants.py`
- `dist/bin/_tasks.py`
- `dist/bin/_features_md.py`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Fase 1 do ADR-0011 implementada. _constants.py: KIND_BUG/KIND_CHORE adicionados, KIND_ISSUE preservado como legacy-read, KIND_LABELS atualizado (bug='Bug / regressao', chore='Chore', issue='Bug (legacy)'). STATUS_BACKLOG='Backlog' adicionado e mapeado em STATUS_TAGS para 'BACKLOG'. PREFIX_DEMANDA='D' + TASK_PREFIXES_FOR_NUMBERING=(D,F,I) introduzidos. TASK_HEADING_RE aceita [DFI]. _tasks.next_task_id: ignora kind e sempre retorna D-NNN com numeracao monotonica considerando max(D,F,I)+1 - garante que D-030 nao colide visualmente com F-029. _features_md.upsert_features_entry: regex de bloco aceita [DFI]. Renderer copiou as 3 mudancas para dist/bin.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- doctor OK; smoke test manual: ai feature 'X' -> D-031 (max(F-030,I-007)+1=31); ai status F-023 (legacy) -> kind=feature resolvido; ai status I-006 (legacy) -> kind=issue resolvido; ai issue 'Y' -> D-032 com kind=issue (sera removido na Fase 4); FEATURES.md renderiza [D-032] com 'Tipo: Bug (legacy)' (KIND_LABELS funcional). Ambos os smoke tests cancelados ao final.

### Validacao pendente

- Nenhuma.

## [F-029] Verbos block/unblock <id> --reason: pausar e retomar task

- **Status:** Validada
- **Origem:** Backlog B-013 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-013: Estado on-hold: task comecada, WIP preservado, fora de acao, vai voltar. Distinto de backlog (nunca comecou), cancelada (terminal) e ready (esperando validacao). STATUS_BLOCKED='Bloqueada' + tag #BLOQUEADA ja existem em _constants.py sem comando. block <id> --reason registra o motivo; unblock <id> volta pra Em desenvolvimento. Funciona com tasks.json multi-task. Custo baixo.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/block.claude.md`
- `core/manifest/bodies/block.agent.md`
- `core/manifest/bodies/unblock.claude.md`
- `core/manifest/bodies/unblock.agent.md`
- `dist/skills/block/SKILL.md`
- `dist/.agents/skills/guia-block/SKILL.md`
- `dist/skills/unblock/SKILL.md`
- `dist/.agents/skills/guia-unblock/SKILL.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: STATUS_BLOCKED e tag BLOQUEADA ja existem em _constants.py sem caminho de transicao no CLI. Distinto de cancel (terminal) e ready (entrega para validacao). Custo baixo: vocabulario ja existe.
- Subcomandos 'block <id> --reason' e 'unblock <id> [--note]' implementados em _cli_lifecycle.py no mesmo lote que cancel (F-027) - compartilham _TERMINAL_STATUSES, find_task_or_current, save_task, set_current_task, write_report, upsert_features_entry. block muda status para Bloqueada, registra em task.blocks[] (reason+at); falha se ja bloqueada ou terminal. unblock muda para Em desenvolvimento, fecha task.blocks[-1].unblockedAt; --note opcional; falha se nao estava bloqueada. Parsers registrados em guia.py com --reason required em block. Novos verbos no manifest.yaml com prefixos 'PAUSE in-flight task' e 'RESUME a paused task' + bodies bodies/{block,unblock}.{claude,agent}.md.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- Smoke test manual completo no caminho feliz: criada F-028 -> block --reason -> tag #BLOQUEADA + task.blocks[0]={reason,at} -> tentativa double-block bloqueada ('ja esta bloqueada') -> unblock --note -> tag #DEV + task.blocks[0].unblockedAt -> cancel --reason -> tag #CANCELADA + current-task limpa. Doctor OK; render-skills check OK (47 alvos).

### Validacao pendente

- Nenhuma.

## [F-028] SMOKE: validar block/unblock/cancel

- **Status:** Cancelada
- **Origem:** Guia Fluxo (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Demanda descartavel criada para smoke test do ciclo block/unblock/cancel. Sera cancelada no fim.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Bloqueada em 2026-06-06: smoke test bloqueio
- Desbloqueada em 2026-06-06: smoke test unlock
- Cancelada em 2026-06-06: encerrar smoke test

### Validacao feita

- Nenhuma.

### Validacao pendente

- Nenhuma.

## [F-027] Verbo cancel <id> --reason: encerrar task como Cancelada

- **Status:** Validada
- **Origem:** Backlog B-012 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-012: Hoje nao ha como encerrar uma task como 'nao vou fazer'; ela fica pendurada em Em desenvolvimento. STATUS_CANCELLED='Cancelada' e a tag #CANCELADA ja existem em _constants.py sem comando que transite pra eles. Adicionar handler cmd_cancel exigindo --reason (justificativa obrigatoria), limpando current-task/worktree e liberando locks. Custo baixo: vocabulario ja existe.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/cancel.claude.md`
- `core/manifest/bodies/cancel.agent.md`
- `dist/skills/cancel/SKILL.md`
- `dist/.agents/skills/guia-cancel/SKILL.md`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/guia.py`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `docs/reference/cli.md`
- `CLAUDE.md`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: STATUS_CANCELLED e tag CANCELADA ja existem em _constants.py sem caminho de transicao no CLI. Adicionar handler cmd_cancel no _cli_lifecycle.py + entrada no manifest.yaml + bodies + render. Custo baixo: vocabulario ja existe.
- Novo subcomando 'cancel <id> --reason <razao>' implementado em _cli_lifecycle.py: muda status para Cancelada, registra em task.cancellations[], grava summary, limpa pending. Guarda contra cancelar task em estado terminal (Validada/Finalizada/Cancelada). Flag --keep-worktree (default: remove worktree associada se existir). Flag --set-current (default: limpa current-task se a task cancelada era a current). Parser registrado em guia.py com --reason required. Novo verbo no manifest.yaml com prefixo 'TERMINAL CANCEL' + bodies bodies/cancel.{claude,agent}.md. Render-skills regerou 8 alvos (3 SKILL.md pares + 2 .py copies, contando juntos com block/unblock que sairam no mesmo lote).
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\core\bin\guia.ps1 doctor OK; render-skills check OK (47 alvos); smoke test manual: cancel I-006 (Validada) -> erro esperado 'em estado terminal'; cancel F-028 (recem-criada para teste) -> status Cancelada, cancellations[] registrado, current-task limpa via _clear_current_if_matches.

### Validacao pendente

- Nenhuma.

## [F-026] Atualizar docs Diataxis pos-refactor para plugin Claude oficial

- **Status:** Validada
- **Origem:** Backlog B-006 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-006: Apos F-009 + backlog acima estarem mergeados: (1) atualizar docs/tutorials/primeiro-uso.md com '/plugin install' como rota primaria; (2) novo docs/how-to/migrar-do-copy-paste-para-plugin.md; (3) revisar docs/reference/cli.md (operacoes agora tambem como MCP tools); (4) revisar docs/explanation/visao-geral.md (Plugin vs repo agora resolvido - virou plugin); (5) atualizar README.md secao Instalacao; (6) atualizar docs/ROADMAP.md (v0.2 Instalador foi superado por plugin format).

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/ROADMAP.md`
- `README.md`
- `docs/tutorials/primeiro-uso.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Apos F-009 (refactor pra plugin) e itens correlatos mergeados, alguns docs ainda refletem mundo pre-plugin. Itens identificados em B-006 plano original: (1) tutorials/primeiro-uso.md - rota /plugin install; (2) novo how-to migrar-do-copy-paste-para-plugin.md; (3) reference/cli.md - mencionar marketplace+namespace; (4) explanation/visao-geral.md - 'Plugin vs repo' agora resolvido; (5) README.md - instalacao; (6) ROADMAP.md - v0.2 Instalador superada por plugin format. Vou auditar cada um e ajustar onde necessario.
- Tres edicoes focadas: (1) docs/ROADMAP.md reescrito com secao 'Entregue' (F-009, F-011, F-012, F-013 marcados) + 'A caminho' (B-009 marketplace remoto, ai --version, smoke tests) - v0.2 nao aparece mais como pendente porque F-013 substituiu. (2) README.md secao Instalacao - linha falsa 'ainda nao ha instalador automatico' substituida por menção a install.ps1/install.sh como rota oficial cross-agent (Claude/Codex/Antigravity); marketplace remoto vira passo 3 com label '(B-009, planejado)'. (3) docs/tutorials/primeiro-uso.md - adicionada 'Convencao deste tutorial' explicando comando 'ai <sub>' (consumidor) vs '.\core\bin\guia.ps1 <sub>' (dogfood); bootstrap agora aponta hooksPath correto por contexto (.githooks consumidor vs core/hooks dogfood); proximos passos incluem how-to/instalar-em-outro-projeto.md. Demais docs auditados (reference/cli.md, explanation/visao-geral.md, how-to/instalar-em-outro-projeto.md) ja estavam atualizados pos-F-013.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\core\bin\guia.ps1 doctor OK; python core/build/render-skills.py --check OK (41 alvos).

### Validacao pendente

- Nenhuma.

## [F-025] Consolidar AGENTS.md como fonte unica cross-agent; CLAUDE.md vira pointer fino

- **Status:** Validada
- **Origem:** Backlog B-005 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-005: AGENTS.md e padrao Linux Foundation (60k+ repos) adotado por Antigravity nativo + Codex + Claude. Hoje temos CLAUDE.md (briefing Claude) + AGENTS.md (briefing outros) com ~80% duplicado. Consolidar tudo em AGENTS.md e deixar CLAUDE.md como pointer fino com so as especificidades Claude (como /rename, comandos Claude-only). Reduz manutencao e segue o padrao de mercado.

### Arquivos modificados/criados

- `FEATURES.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: AGENTS.md e padrao Linux Foundation (60k+ repos), Antigravity v1.20.3 le nativo. Hoje CLAUDE.md + AGENTS.md tem ~80% duplicado, gerando drift. Plano: enriquecer AGENTS.md com o que falta (verificacao dupla doctor+render --check, secao 'Quando o usuario pedir algo que nao se encaixa', mencao a docs-check) e reduzir CLAUDE.md a pointer + so o que e Claude-especifico (namespace ai, marketplace dist/, /rename, edit/write tool naming).
- AGENTS.md agora explicito como fonte canonica cross-agent + absorveu 'Verificacao antes de entregar' (doctor + render --check) e secao 'Quando o pedido nao se encaixa' que estavam so no CLAUDE.md. CLAUDE.md reescrito como pointer fino: plataforma, plugin/namespace ai, descoberta automatica, especificidades Claude (Edit/Write, /rename, NOME DO CHAT). Conteudo geral (regras, fluxo, commits, comandos, doctor/render check) so vive em AGENTS.md.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\core\bin\guia.ps1 doctor OK; python core/build/render-skills.py --check OK (41 alvos em sincronia).

### Validacao pendente

- Nenhuma.

## [F-024] ADR-0011: repensar modelo de demanda (tipo x status)

- **Status:** Validada
- **Origem:** Backlog B-016 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-016: Pack mistura tipo e status na identidade: F/I=tipo, B=status disfarcado de tipo em arquivo separado. Motor JA modela como entidade unica: cada task tem kind e status em tasks.json. Decidir em ADR: (a) backlog vira status=backlog dentro de tasks.json em vez de backlog.json/B-NNN; (b) unificar feature/issue numa entidade demanda com tipo feature/bug/chore - issue como nome de tipo deixa de existir (colisao com o sentido guarda-chuva de issue na industria), mantendo a distincao feature-vs-bug (CHANGELOG Added/Fixed, relatorios). Decisao-raiz: Planejada e current-task dependem dela. ADR primeiro, refactor depois.

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/adr/0011-modelo-de-demanda-tipo-x-status.md`
- `docs/adr/README.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Pack hoje mistura tipo e status: F/I prefixo carrega tipo, B-NNN e status (backlog) disfarcado de tipo em arquivo separado, e o nome 'issue' colide com o sentido guarda-chuva da industria. Motor ja modela kind+status em tasks.json. Precisamos da decisao escrita ANTES de refatorar - B-017 (Planejada) e B-018 (current-task) dependem dela.
- ADR-0011 (status Proposta) escrito: kind+status como eixos ortogonais, backlog vira status dentro de tasks.json, issue (tipo restrito) substituido por bug, ID neutro D-NNN. Indice em docs/adr/README.md atualizado. Sem mudanca de codigo ou comportamento - refactor concreto fica para uma feature posterior que herda decisao deste ADR.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- ADR segue template (Contexto/Decisao/Consequencias/Alternativas/Links); indice da README.md inclui linha 0011.

### Validacao pendente

- Nenhuma.

## [F-023] Doc: deixar explicito que ready e disparado pela IA, nao pelo humano

- **Status:** Validada
- **Origem:** Backlog B-015 (2026-06-06)
- **Tipo:** Feature
- **Contexto:** Backlog B-015: Mal-entendido recorrente: ready parece o humano avisando que vai validar, mas e a IA que roda ao terminar de codar, sinalizando handoff. ready e o gate antes do finish (forca humano-no-loop; validate foi depreciado em F-003 por isso). Documentar nos bodies/docs pra nao induzir a remover o verbo. So doc, sem codigo.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/ready.claude.md`
- `core/manifest/bodies/ready.agent.md`
- `dist/skills/ready/SKILL.md`
- `dist/.agents/skills/guia-ready/SKILL.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/guia.py`
- `docs/ROADMAP.md`
- `docs/adr/README.md`
- `docs/tutorials/primeiro-uso.md`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Verbo ready confunde porque parece o humano avisando que vai validar. Na verdade a IA roda ready ao terminar de codar - e o handoff que forca human-in-the-loop antes de finish. Aclarar bodies (ready.claude.md/ready.agent.md) e descriptions ja ajuda muito; impacto minimo, so doc.
- Adicionado paragrafo inicial nos dois bodies do ready deixando explicito que a IA dispara o verbo ao terminar de codar (nao o humano), e que ready e o gate antes do finish. Reforco no description do ready em manifest.yaml. Render-skills regerou os dois SKILL.md.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\core\bin\guia.ps1 render OK; .\core\bin\guia.ps1 doctor OK.

### Validacao pendente

- Nenhuma.

## [I-007] Encerrar B-001: marketplace.json ja existe no repo

- **Status:** Validada
- **Origem:** Backlog B-001 (2026-06-06)
- **Tipo:** Issue / regressao
- **Contexto:** Backlog B-001: Pos F-009. Cria marketplace proprio (pmarcos/guia-fluxo) para usuarios instalarem via '/plugin marketplace add pmarcosa/guia-fluxo' + '/plugin install guia-fluxo@pmarcos'. Define name, version, owner, plugins[]. Atualizar docs/how-to/instalar-em-outro-projeto.md e README com a nova rota oficial.

### Arquivos modificados/criados

- `FEATURES.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: dist/.claude-plugin/marketplace.json ja foi criado em F-009. Parte de documentacao remanescente foi absorvida por B-006 (atualizar docs Diataxis pos refactor). Item duplicado/superseded.
- Sem implementacao: marketplace.json ja em dist/.claude-plugin/; docs delegadas para B-006.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- Test-Path dist/.claude-plugin/marketplace.json confirma existencia.

### Validacao pendente

- Nenhuma.

## [I-006] Encerrar investigacao do gap de slash commands /guia:*

- **Status:** Validada
- **Origem:** Backlog B-010 (2026-06-06)
- **Tipo:** Issue / regressao
- **Contexto:** Backlog B-010: Validacao parcial de F-009 detectou que apos instalar o plugin ai@guia-fluxo via marketplace local, a system-reminder de skills disponiveis no Claude listou APENAS ai:guia-fluxo. As 7 shims (feature, issue, backlog, promote, ready, finish, status) - presentes em skills/<verbo>/SKILL.md gerados pelo render - nao apareceram. Resultado pratico: /guia:finish retorna 'Unknown command'. Hipoteses a investigar: (a) reload de plugin faltando, (b) cache do Claude Code corrompido, (c) frontmatter dos shims requer flag explicito (disable-model-invocation, ou outro campo), (d) versao do Claude Code (verificar se 2.1.142+), (e) limitacao do plugin de descobrir multiplas skills em pasta skills/ vs single-skill. Reproduzir e propor fix.

### Arquivos modificados/criados

- `FEATURES.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Sintoma original (plugin so listava ai:guia-fluxo) nao se reproduz mais: instalacao via marketplace local ./dist com extraKnownMarketplaces ja expoe /guia:feature, /guia:issue, /guia:backlog, /guia:promote, /guia:ready, /guia:finish, /guia:status corretamente. Provavelmente foi cache/reload na primeira tentativa. Sem ganho em manter item aberto.
- Sem implementacao: gap nao reproduz mais; plugin local-marketplace lista todas as shims.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- Sessao atual confirma: skills ai:feature/issue/backlog/promote/ready/finish/status disponiveis.

### Validacao pendente

- Nenhuma.

## [F-022] ADRs canonicos: YAML para manifest + prefixos de trigger

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 1.Q1 (escolha tacita de YAML para o manifest sem ADR justificando; documentar trade-offs vs JSON/TOML/N-arquivos e o caso 'on:->True' do PyYAML 1.1) e 1.6 (prefixos PRIMARY TRIGGER/DEFER-AND-PARK/READ-ONLY/etc. nas descriptions vivem so no commit da F-003 e na PR original; sem ADR proximo editor pode quebrar). Cria ADR-0009 (YAML para manifest) e ADR-0010 (prefixos de trigger).

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/adr/0009-yaml-para-manifest.md`
- `docs/adr/0010-prefixos-trigger-skill-descriptions.md`
- `docs/adr/README.md`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- ADR-0009 documenta retroativamente YAML para manifest com tradeoffs vs JSON/TOML/N-arquivos, caso real 'on:->True' do PyYAML 1.1 (com workaround ja em _docs_hook), e quando reconsiderar.
- ADR-0010 formaliza 7 prefixos canonicos (PRIMARY TRIGGER, DEFER-AND-PARK, EVALUATE-AND-CONVERT, HANDOFF, CLOSE, READ-ONLY, REFERENCE/BACKGROUND ONLY) instituidos por F-003 + clausula 'Do NOT use for' linkando skills vizinhas.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK
- python -m unittest discover -s tests -> Ran 101 tests, OK

### Validacao pendente

- Nenhuma.

## [F-021] Wrappers e bodies polish: Invoke-PythonScript no guia.ps1 + fallback python nos bodies

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 3.11 (logica especial do launcher py duplicada em guia.ps1 - tem em Test-PythonVersion e na invocacao do script; centralizar em Invoke-PythonScript) e 1.9 (bodies das skills citam apenas .core/bin/guia.ps1 sem mencionar o fallback portavel python core/src/guia.py para Linux/Mac).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/bin/guia.ps1`
- `core/manifest/bodies/feature.claude.md`
- `core/manifest/bodies/issue.claude.md`
- `core/manifest/bodies/backlog.claude.md`
- `core/manifest/bodies/promote.claude.md`
- `core/manifest/bodies/ready.claude.md`
- `core/manifest/bodies/finish.claude.md`
- `core/manifest/bodies/status.claude.md`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `dist/bin/guia.ps1`
- `dist/skills/backlog/SKILL.md`
- `dist/skills/feature/SKILL.md`
- `dist/skills/finish/SKILL.md`
- `dist/skills/issue/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `dist/skills/ready/SKILL.md`
- `dist/skills/status/SKILL.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- guia.ps1 ganha Get-PythonInvocation (normaliza py -3) e Invoke-PythonRaw (executa sem coletar stdout - bug classico do PowerShell). Aplicado em Test-PythonVersion e no bloco final. Anti-regressao explicita no docstring.
- 7 bodies de claude_skill (feature/issue/backlog/promote/ready/finish/status) ganham linha 'Portable fallback (Linux/Mac/sem PowerShell): python core/src/guia.py <verbo>...'.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> Ran 101 tests, OK
- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK
- python core/build/render-skills.py -> 7 SKILL.md rerendered

### Validacao pendente

- Nenhuma.

## [F-020] Check-lock polish: --dry-run em lock, --force em unlock, stdin em ci

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 5.16 (--dry-run em cmd_lock para preview sem gravar), 5.11 (cmd_unlock exige --force ou prompt para confirmar a operacao permanente), 5.12 (cmd_ci aceita stdin via files=- messages=- para pipelines).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/lock/check-lock.py`
- `tests/test_check_lock_polish.py`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- 3 capacidades novas no check-lock CLI: (1) lock --dry-run valida invariantes (id existente, lock-ignore, path traversal) e imprime previa sem gravar registry; (2) unlock --force pula confirmacao; sem --force em non-TTY aborta antes de mexer, em TTY pede confirmacao digitando o id; (3) ci aceita - como path em --files/--messages -> stdin. Helper _read_input_or_file centraliza a logica.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> Ran 101 tests, OK
- lock --dry-run mostra preview e --check-orphans sai zero (registry intacto)
- unlock sem --force em subprocess (non-TTY) retorna 1 sem mutar

### Validacao pendente

- Nenhuma.

## [F-019] Render polish: --clean, --output-dir, frontmatter extras, shared_body explicito

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 4.Q3 (--clean real para apagar orfaos), 4.5 (--output-dir configuravel), 4.11 (frontmatter extras como allowed-tools/model), 1.5 (shared_body explicito via campo dedicado em vez de body_file duplicado). Tudo no core/build/render-skills.py mantendo backward compat.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `tests/test_render_polish.py`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Render-skills ganha 4 capacidades: (1) --clean apaga orfaos + diretorios vazios apos render (com filtro para __pycache__/.pytest_cache); (2) --output-dir reaponta DIST_DIR via _retarget_dist em runtime, --check tambem respeita; (3) frontmatter extras: verbs.X.frontmatter aceita allowed-tools/model com sanity check (name/description reservados); (4) shared_body explicito: verbs.X.shared_body aponta body unico aplicado a TODOS targets sem body_file proprio.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> Ran 96 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvos
- python core/build/render-skills.py --output-dir <tmp> -> 41 arquivos gerados em pasta custom
- --check-orphans antes listava 18 .pyc; agora ignora __pycache__ e diz 'OK: nenhum orfao'

### Validacao pendente

- Nenhuma.

## [F-018] Hardening: doctor estendido, check-lock info/edit/history/--json, dedup hook commit-msg

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 2.10 (doctor so checa 4 arquivos), 5.Q2 (check-lock sem info/edit/history), 5.Q3 (sem flag --json) e 6.Q1 (core/hooks/commit-msg e core/templates/.githooks/commit-msg sao byte-identicos sem deduplicacao). Esta feature implementa: (1) doctor estende verificacoes (manifest YAML carregavel, PyYAML disponivel, git no PATH, render --check OK, dist/ alinhado, lock_api importavel); (2) check-lock ganha 3 subcomandos novos (info <id>, edit <id> --add-file ..., history <id>); (3) check-lock list/check/audit/info aceitam --json; (4) core/templates/.githooks/commit-msg vira copia gerada pelo renderer a partir de core/hooks/commit-msg (fonte unica).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/guia.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `core/build/render-skills.py`
- `tests/test_check_lock_info_edit_history.py`
- `tests/test_doctor_extended.py`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/guia.py`
- `dist/bin/lock_api.py`

### O que foi feito

- Demanda criada via guia-fluxo.
- doctor estendido: checa manifest YAML carregavel, PyYAML, git no PATH, render --check, dist/bin/guia.py, lock_api importavel. Flags --strict (warning vira erro) e --skip-render (CI rapido). Detecta layout consumer (sem core/) via _is_dev_repo e degrada para modo 'lite' que so checa .guia/ + git.
- check-lock ganhou 3 subcomandos: info <id> (detalhes), edit <id> --add-file/--remove-file/--description (preserva id+locked_at), history <id> (git log filtrado por [unlock:<id>]).
- Flag --json adicionada em list/check/info/audit/history do check-lock. Payload coerente com schema (count, locks, ok, blocked, etc.).
- lock_api ganhou get_lock(id) e edit_lock(id, add/remove/description) com excecoes proprias (LockNotFound, LockIgnoredPath, LockOutsideRepo) reutilizadas pelo CLI.
- Dedup commit-msg: core/templates/.githooks/commit-msg apagado. Renderer ganhou PROMOTED_TEMPLATES que copia core/hooks/commit-msg direto para dist/templates/.githooks/commit-msg. Fonte unica em core/hooks/.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> Ran 90 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvo(s)
- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK
- check-lock info adicoes-exigem-autorizacao -> detalhes do lock global
- check-lock history adicoes-exigem-autorizacao -> 8 commits encontrados (todos os com unlock no historico)

### Validacao pendente

- Nenhuma.

## [F-017] Subcomandos tasks list/show/filter para navegacao do .guia/tasks.json

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achado 2.11: o CLI hoje so tem 'status' (uma task por vez via current ou ID). Falta forma rapida de listar tudo, filtrar por status/kind, e ver detalhe de uma task arbitraria sem mexer em current. Proposta: subcomando 'tasks' com 'list', 'show <ID>', 'filter --status X --kind Y --limit N'. Saida texto humana + flag --json para consumo por agente. Reaproveita _tasks.find_task, recent_task_ids; adiciona _tasks.list_tasks(filter) e _tasks.format_task_line.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_tasks.py`
- `core/src/_cli_tasks.py`
- `core/src/guia.py`
- `tests/test_tasks_list.py`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `dist/bin/_tasks.py`
- `dist/bin/guia.py`

### O que foi feito

- Demanda criada via guia-fluxo.
- Subcomando 'tasks' adicionado com 3 acoes: list/show/filter. list aceita --limit N; show <ID> retorna exit 1 se nao encontra; filter combina --status/--kind/--limit. Todos suportam --json. Helpers: _tasks.list_tasks(status,kind,limit) e _tasks.format_task_line(task). Subcomando registrado em guia.py.build_parser usando STATUS_* e KIND_* de _constants (sem strings magicas).
- Tests novos em test_tasks_list.py: 8 casos (3 list, 2 show, 3 filter) exercitando sandbox completo com init+feature+issue+ready. Total da suite: 77 testes.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> Ran 77 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvo(s)
- .\core\bin\guia.ps1 tasks list --limit 5 -> lista corretamente as 5 mais recentes
- .\core\bin\guia.ps1 tasks show F-016 --json -> retorna task completa em JSON

### Validacao pendente

- Nenhuma.

## [F-016] Layout B do manifest: index YAML + bodies markdown em core/manifest/bodies/

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 Etapa 1 Q2 (aprovada): migrar core/manifest/manifest.yaml (arquivo unico 422 linhas) para layout B. Index YAML curto declara verbos, descriptions e referencia body_file/shared_body. Bodies viram arquivos markdown puros em core/manifest/bodies/<verb>.<target>.md. Renderer atualizado para resolver body_file (le do disco), shared_body (uma vez, reusa). Deliverable: manifest.yaml ~80 linhas + 14 bodies markdown + renderer estendido + smoke tests do schema novo. Saida SKILL.md em dist/ permanece byte-identica.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/guia-fluxo.agent.md`
- `core/manifest/bodies/guia-fluxo.claude.md`
- `core/manifest/bodies/feature.agent.md`
- `core/manifest/bodies/feature.claude.md`
- `core/manifest/bodies/issue.agent.md`
- `core/manifest/bodies/issue.claude.md`
- `core/manifest/bodies/backlog.agent.md`
- `core/manifest/bodies/backlog.claude.md`
- `core/manifest/bodies/promote.agent.md`
- `core/manifest/bodies/promote.claude.md`
- `core/manifest/bodies/ready.agent.md`
- `core/manifest/bodies/ready.claude.md`
- `core/manifest/bodies/finish.agent.md`
- `core/manifest/bodies/finish.claude.md`
- `core/manifest/bodies/status.agent.md`
- `core/manifest/bodies/status.claude.md`
- `core/build/render-skills.py`
- `tests/test_manifest_layout_b.py`
- `docs/adr/0008-layout-b-manifest.md`
- `docs/adr/README.md`
- `CHANGELOG.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Layout B implementado: manifest.yaml passa de 422 linhas (bodies inline) para ~80 linhas (index com body_file:). 16 bodies extraidos como markdown puro em core/manifest/bodies/<verb>.<target>.md. Schema v2: body_file aponta path relativo a core/manifest/, renderer valida existencia + recusa path traversal + cacheia leituras (shared_body trivial). Backward compat com body inline v1 mantida. Saida dist/ byte-identica - confirmado por --check 40 alvos.
- Tests: 4 novos casos em test_manifest_layout_b.py validam schema (version 2, body_file presente, files existem, sem orfaos em bodies/). Total da suite: 69 testes.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python core/build/render-skills.py --check -> OK: 40 alvo(s) em sincronia
- python -m unittest discover -s tests -> Ran 69 tests in 12.5s, OK
- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK

### Validacao pendente

- Nenhuma.

## [I-005] Bugs e melhorias do CLI/check-lock identificados na auditoria F-014

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Issue / regressao
- **Contexto:** Cobre achados 2.1 (cleanup duplicado), 2.2 (promote grava antes de criar), 2.4 (paths Windows nao normalizados em commit_task), 2.5 (mensagem 'task not found' sem hint), 2.9 (--no-commit removia worktree), 2.12 (git ausente sem msg clara), 2.13 (attach_worktree sem pre-check de branch), 2.Q2 (validate deprecated sem warning), 5.3 (audit silencioso fora de repo), 5.10 (cmd_lock sem --allow-missing), 5.14 (UNLOCK_RE sem validacao de motivo), 5.19 (path traversal em _norm), 5.2 (sem cache em _load_lock_ignore). Implementado dentro do refactor F-015.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_creation.py`
- `core/src/_commit.py`
- `core/src/_worktree.py`
- `core/src/_tasks.py`
- `core/src/_cli_lifecycle.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `.guia/backlog.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Corrigidos no refactor F-015: 2.1 cleanup_task_worktree chamado uma vez so; 2.2 cmd_promote constroi task+worktree antes de mutar backlog; 2.4 _commit.commit_task normaliza paths via _paths.normalize_path; 2.5 find_task_or_current sugere recent_task_ids; 2.9 cleanup pula quando --no-commit; 2.12 has_git + MSG_GIT_NOT_FOUND em git_ops; 2.13 git_branch_exists pre-check em attach_worktree; 2.Q2 cmd_validate imprime warning de deprecacao; 5.3 cmd_audit pre-checa .git/; 5.10 cmd_lock aceita --allow-missing; 5.14 unlocked_ids exige MOTIVO_RE; 5.19 add_lock valida path traversal via _path_inside_repo; 5.2 _load_lock_ignore_cached via lru_cache.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests -> 63 testes OK
- .\core\bin\guia.ps1 doctor -> OK
- python core\build\render-skills.py --check -> OK 40 alvos

### Validacao pendente

- Nenhuma.

## [F-015] Refactor SOLID/Clean Arch do core (constantes + lock_api + split modular)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 etapa 8 cluster A+B+C: centralizar strings/paths em _constants, extrair lock_api importavel (remove duplicacao 2.Q3+5.Q1, corrige bug latente lock_task_files), decompor core/src/guia.py em domain/infrastructure/cli mantendo dist/bin/ standalone via renderer que copia pacote inteiro. SOLID: SRP por modulo, OCP nos comandos via dispatch table, DIP via injecao de filesystem nos services.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_constants.py`
- `core/src/_state.py`
- `core/src/_paths.py`
- `core/src/_clock.py`
- `core/src/_git_ops.py`
- `core/src/_tasks.py`
- `core/src/_features_md.py`
- `core/src/_process_config.py`
- `core/src/_docs_hook.py`
- `core/src/_locks.py`
- `core/src/_worktree.py`
- `core/src/_commit.py`
- `core/src/_reports.py`
- `core/src/_validation_runner.py`
- `core/src/_cli_lifecycle.py`
- `core/src/_cli_creation.py`
- `core/src/_cli_meta.py`
- `core/src/guia.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `core/build/render-skills.py`
- `core/bin/ai`
- `core/bin/guia.ps1`
- `core/manifest/manifest.yaml`
- `tests/conftest_paths.py`
- `tests/test_smoke.py`
- `tests/test_constants.py`
- `tests/test_paths.py`
- `tests/test_tasks_domain.py`
- `tests/test_features_md.py`
- `tests/test_docs_hook.py`
- `tests/test_lock_api.py`
- `tests/test_render_skills.py`
- `tests/test_check_lock_cli.py`
- `tests/test_cli_promote_order.py`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `dist/.agents/skills/guia-finish/SKILL.md`
- `dist/.agents/skills/guia-promote/SKILL.md`
- `dist/bin/guia.ps1`
- `dist/bin/guia.py`
- `dist/skills/feature/SKILL.md`
- `dist/skills/issue/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `docs/adr/README.md`
- `docs/adr/0007-arquitetura-modular-core-src.md`
- `docs/auditorias/F-014-validacao.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Refactor SOLID/Clean Architecture/DDD do core: 17 novos modulos sob core/src/_*.py (constants, state, paths, clock, git_ops, tasks, features_md, process_config, docs_hook, locks, worktree, commit, reports, validation_runner, cli_lifecycle, cli_creation, cli_meta) + lock_api em core/lock/. guia.py reduzido de 965 para ~205 linhas (so wiring + parser). check-lock.py reduzido a CLI fino sobre lock_api. render-skills.py hardened com dataclass Output, --check-orphans, abortar em marker ausente, validacao YAML. Wrappers: guia.ps1 com Resolve-Python em camadas + validacao versao 3.10+ + diagnostico rico + glob de Python3*; core/bin/guia POSIX simetrico. Bodies do manifest alinhados ao CLI (--context, worktree branch codex/<slug>, rodape guia-fluxo em promote/finish).
- Achados implementados: A (constants), B (lock_api), C (split modular), D (1,2,4,5,9,12,13,Q2), E (Q1,Q2,4,5,6,8), F (3,6,Q2,Q3,12,17), G (1,3,8), H (3,10,14,19,2). Total ~28 dos 90 achados endereco direto, mais alguns indiretos por centralizacao.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest discover -s tests: 63 testes em 6.3s, OK
- .\core\bin\guia.ps1 doctor: Guia Fluxo files OK
- python core\build\render-skills.py --check: OK 40 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [F-014] Auditoria estruturada de core/ para mapear features, issues e backlog

- **Status:** Em desenvolvimento
- **Origem:** Guia Fluxo (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Walkthrough em 7 etapas (manifest, guia.py, guia.ps1, render-skills.py, check-lock.py, hooks, templates) de cada arquivo em core/. Para cada arquivo: funcao atual, riscos, melhorias, possiveis adicoes. Saida: lista de candidatos classificados como feature/issue/backlog para abertura em lote ao final. Inclui doc de acompanhamento em docs/explanation/ para rastrear progresso entre sessoes e fora do chat.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via guia-fluxo.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


## [F-013] B-008 passos 3+4: install.ps1/install.sh + templates em dist/ + smoke do consumer

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Continuacao direta de F-012 (que entregou passos 1+2 de B-008: renderer com prefixo ai- + dist/bin/ standalone). Faltam: (a) install.ps1 + install.sh na raiz do repo-mae que copia dist/.claude-plugin/ + dist/skills/ + dist/bin/ -> consumer/.guia-fluxo/, dist/.agents/skills/ -> consumer/.agents/skills/, e dispara 'ai init' pra semear .guia/ + FEATURES.md. (b) Templates em dist/templates/ (.githooks/commit-msg, features/registry.yaml, features/lock-ignore.txt) que o instalador opcionalmente copia. (c) Atualizar docs/how-to/instalar-em-outro-projeto.md com a rota install.ps1. (d) Smoke test estendido pra simular install num tempdir + 'ai doctor' do .guia-fluxo/bin/ e validar layout final. Decisao tecnica: install.ps1 sera idempotente (re-rodar sobrescreve dist/* mas preserva .guia/ existente) e --dry-run para previsualizar. Dogfood do repo-mae nao e tocado nesta feature - fica como follow-up separado (criar symlink .agents -> dist/.agents no proprio repo ou install loopback).

### Arquivos modificados/criados

- `FEATURES.md`
- `install.ps1`
- `install.sh`
- `core/build/render-skills.py`
- `dist/templates/.githooks/commit-msg`
- `dist/templates/features/registry.yaml`
- `dist/templates/features/lock-ignore.txt`
- `tests/test_install.py`
- `docs/how-to/instalar-em-outro-projeto.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`
- `CHANGELOG.md`
- `docs/explanation/visao-geral.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Renderer estendido para empacotar templates em dist/templates/: copia core/templates/.githooks/commit-msg, core/templates/features/registry.yaml e core/templates/features/lock-ignore.txt mantendo layout 1:1. Total de alvos cobertos passou de 19 para 22.
- install.ps1 na raiz: copia idempotente de dist/* para o consumer (.guia-fluxo/ recebe .claude-plugin/+skills/+bin/; .agents/skills/ vai pra raiz do consumer; templates vao pra .githooks/ e features/ preservando customizacao - use -Force pra sobrescrever). Roda 'python .guia-fluxo/bin/guia.py init' ao final. Flags -Target, -DryRun, -Force, -SkipInit. Validado dry-run e real install em tempdir.
- install.sh paridade comportamental: mesmas flags em formato POSIX (--target, --dry-run, --force, --skip-init), mesmo mapa de copia via cp -R, chmod +x automatico em .githooks/commit-msg e .guia-fluxo/bin/ai.
- tests/test_install.py: 3 casos cobrindo (a) layout completo apos install + frontmatter ai-feature/guia-fluxo + doctor exit 0 do consumer; (b) shim POSIX LF puro (anti-regressao); (c) wrapper ps1 aponta pra guia.py local (nao ..\\src\\guia.py). Roda cross-platform porque replica logica do installer em Python puro.
- docs/how-to/instalar-em-outro-projeto.md reescrito: TL;DR com install.ps1/install.sh, layout final, tabela de flags, secao 'idempotencia', upgrade flow, desinstalar, mapa por agente, fallback copia-manual.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python core/build/render-skills.py --check -> OK 22 alvo(s).
- python -m unittest tests.test_smoke tests.test_install -v -> Ran 4 tests, OK (smoke base + 3 novos do install).
- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK.
- install.ps1 -DryRun em tempdir: lista as 9 operacoes de copia + init sem escrever; install real em tempdir: cria todos os 28 arquivos esperados; 'python .guia-fluxo/bin/guia.py doctor' do consumer retorna Guia Fluxo files OK.
- test_install valida: name: ai-feature no frontmatter cross-tool, name: guia-fluxo sem duplo prefixo, sem skills 'feature' (sem prefixo) em .agents/skills/, shim POSIX e LF puro.

### Validacao pendente

- Nenhuma.

## [F-012] B-008: Passo 2 - Layout .guia-fluxo/ no consumidor com bin/ e prefixo ai- nas skills cross-tool

- **Status:** Validada
- **Origem:** Backlog B-008 (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Backlog B-008: Migrar projeto consumidor pro layout: 3 pastas (.agents/, .claude/, .guia-fluxo/) + raiz (.guia/, FEATURES.md, opcional features/). Especifico: (a) plugin Claude inteiro dentro de .guia-fluxo/ com .claude-plugin/, skills/ (nomes curtos feature, issue, etc.) e bin/ (motor ai/guia.ps1 que vira PATH automaticamente segundo doc Anthropic - feature ja existente). (b) Codex/Antigravity em .agents/skills/ com prefixo ai- nos nomes (ai-feature, ai-issue, etc.) pra evitar colisao - decisao confirmada com user em F-009. (c) Renderer adaptado pra gerar 2 outputs com nomes diferentes. (d) instalador install.ps1 + install.sh que copia dist/ pra .guia-fluxo/ no consumidor + inicializa .guia/. Depende de B-007 (Passo 1).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `dist/.agents/skills/guia-fluxo/SKILL.md`
- `dist/.agents/skills/guia-feature/SKILL.md`
- `dist/.agents/skills/guia-issue/SKILL.md`
- `dist/.agents/skills/guia-backlog/SKILL.md`
- `dist/.agents/skills/guia-promote/SKILL.md`
- `dist/.agents/skills/guia-ready/SKILL.md`
- `dist/.agents/skills/guia-finish/SKILL.md`
- `dist/.agents/skills/guia-status/SKILL.md`
- `dist/bin/guia.py`
- `dist/bin/guia.ps1`
- `dist/bin/ai`
- `CHANGELOG.md`
- `docs/explanation/visao-geral.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Feature: nova capacidade (gerador estendido + instalador + layout consumer). F-011 entregou core/+dist/ (lado dev); B-008 fecha lado consumer (.guia-fluxo/+.agents/skills com prefixo ai-+install.ps1/.sh). Acionavel - F-009 ja confirmou prefixo ai-, dependencia B-007 entregue, deliverables claros.
- Renderer estendido (core/build/render-skills.py) com 2 mudancas: (1) prefixo ai- aplicado no nome do diretorio E no frontmatter name: dos arquivos .agents/skills/ai-<verb>/SKILL.md cross-tool (Codex+Antigravity); excecao para verbo guia-fluxo que ja carrega o prefixo (helper agent_skill_name). Output Claude (dist/skills/<verb>/) inalterado pois namespace ai: do plugin ja qualifica os atalhos como /guia:feature etc. (2) Renderer agora copia core/src/guia.py -> dist/bin/guia.py (motor) e core/bin/guia.ps1 -> dist/bin/guia.ps1 (com path adaptado via _adapt_wrapper_for_plugin: ..\src\guia.py reescrito para guia.py), e gera shim POSIX dist/bin/ai. Total de alvos cobertos por --check passou de 16 para 19.
- Fix de newline (F-007 follow-up): write_text agora usa newline="\n" para evitar traducao automatica de \n para CRLF no Windows. Critico para o shim POSIX (bash quebra com CRLF: bash\r: not found) e coerente com normalizacao do .gitattributes (eol=lf default; *.ps1 eol=crlf re-aplicado no checkout).
- Docs: CHANGELOG.md ganhou entry Unreleased/Changed descrevendo F-012; docs/explanation/visao-geral.md atualizada (dist/ inclui bin/, .agents/skills/ai-<verb>, item 5 do roadmap marca passos 1+2 entregues e installer pendente).
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python core/build/render-skills.py --check -> OK: 19 alvo(s) em sincronia com o manifest.
- python -m unittest tests.test_smoke -v -> Ran 1 test in 1.057s, OK.
- .\core\bin\guia.ps1 doctor -> Guia Fluxo files OK.
- .\dist\bin\guia.ps1 doctor -> Guia Fluxo files OK (wrapper standalone valida que rewriting do path guia.py funciona).
- Bytes do shim POSIX dist/bin/guia: LF puro (verificado via [System.IO.File]::ReadAllBytes).
- Frontmatter inspecionado: dist/.agents/skills/guia-feature/SKILL.md tem 'name: ai-feature'; dist/.agents/skills/guia-fluxo/SKILL.md tem 'name: guia-fluxo' (sem duplo prefixo); dist/skills/feature/SKILL.md tem 'name: feature' (sem prefixo).

### Validacao pendente

- Nenhuma.

## [F-011] B-007: Passo 1 - Reorganizar repo do pack em core/ (dev) + dist/ (buildado)

- **Status:** Validada
- **Origem:** Backlog B-007 (2026-06-01)
- **Tipo:** Feature
- **Contexto:** Backlog B-007: Refactor interno do repo-mae: mover scripts/, plugin-src/, bin/, .githooks/, templates/ pra dentro de core/ (com subpastas src/, manifest/, build/, lock/, hooks/, templates/). Criar dist/ como saida buildada que espelha o layout do consumidor. Nao muda nada no projeto consumidor ainda - continua copia manual. Beneficio: limpa o repo-mae, separa fabrica de produto, prepara terreno pro Passo 2. Estimativa: refactor amplo, mexe em paths em todas as docs/CI/wrappers/testes.

### Arquivos modificados/criados

- `FEATURES.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/docs-map.yaml`
- `.guia/tasks.json`
- `.editorconfig`
- `.gitattributes`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/lock-check.yml`
- `.github/workflows/render-check.yml`
- `AGENTS.md`
- `CHANGELOG.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `README.md`
- `SECURITY.md`
- `core/build/render-skills.py`
- `core/hooks/commit-msg`
- `core/lock/check-lock.py`
- `core/manifest/manifest.yaml`
- `core/src/guia.py`
- `core/templates/.githooks/commit-msg`
- `core/templates/features/lock-ignore.txt`
- `core/templates/features/registry.yaml`
- `docs/adr/0001-script-fonte-da-verdade.md`
- `docs/adr/README.md`
- `docs/explanation/por-que-lock.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/auditar-desbloqueios.md`
- `docs/how-to/configurar-hooks-git.md`
- `docs/how-to/destravar-arquivo.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `docs/how-to/renomear-arquivo-travado.md`
- `docs/how-to/travar-arquivo.md`
- `docs/reference/cli.md`
- `docs/reference/docs-map.md`
- `docs/reference/files.md`
- `docs/reference/hooks-git.md`
- `docs/reference/registry-yaml.md`
- `docs/reference/troubleshooting.md`
- `docs/tutorials/primeiro-uso.md`
- `features/registry.yaml`
- `scripts/guia.ps1`
- `tests/test_smoke.py`
- `core/bin/guia.ps1`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/how-to/promover-backlog.md`
- `docs/adr/0006-plugin-oficial-claude-code.md`

### O que foi feito

- Backlog promovido via guia-fluxo.
- Avaliacao IA: Refactor estrutural amplo: mover scripts/, plugin-src/, .githooks/, templates/, bin/ para core/{src,manifest,build,lock,hooks,templates} e criar dist/ como saida buildada espelhando o layout do consumidor. Separa fabrica de produto, prepara B-008/B-009. Acionavel - destino e origem claros no contexto.
- Repo-mae reorganizado em core/ (src, build, manifest, lock, hooks, templates) + dist/ (.claude-plugin, skills, .agents/skills). Self-dogfood preservado: .claude/settings.json aponta marketplace pra ./dist, marketplace.json plugin source = ../, git core.hooksPath = core/hooks. Wrapper scripts/guia.ps1 mantido e roteia pra core/src/guia.py. Render-skills.py adaptado, CI atualizada, smoke test atualizado, todos docs com paths novos. ADRs 0001 e 0006 com nota de atualizacao por F-011.
- Ajuste adicional pos-review: guia.ps1 movido de scripts/ pra core/bin/ (cumpre B-007 estritamente). Pasta scripts/ removida. Wrapper atualizado pra resolver core/src/guia.py via ..\src\guia.py e .venv via ..\..\.venv. Todas as referencias em docs/manifest/settings substituidas: .\scripts\guia.ps1 -> .\core\bin\guia.ps1 e scripts/guia.ps1 -> core/bin/guia.ps1.
- F-011 entregue. Refactor estrutural concluido: core/ (src, bin, build, manifest, lock, hooks, templates) + dist/ (.claude-plugin, skills, .agents/skills). scripts/ removida. guia.ps1 final em core/bin/guia.ps1. Wrapper testado, smoke test passa, render --check passa, doctor passa. Docs sincronizadas com novos paths (3 ADRs + 6 explanation/reference + 7 how-to + 1 tutorial + CHANGELOG + briefings + raiz). Limitacao: reinstall do plugin Claude (/plugin marketplace add ./dist) precisa de sessao nova - fica pra teste manual. Commit deixado para passo separado por causa do lock global adicoes-exigem-autorizacao.

### Validacao feita

- doctor: Guia Fluxo files OK. render --check: OK 16 alvo(s) em sincronia. tests/test_smoke.py: ok (Ran 1 test in 0.857s). docs-check F-011: lista 10 candidatos, todos ja atualizados nesta entrega. core.hooksPath = core/hooks.
- Limitacao conhecida: reinstall do plugin no Claude Code (/plugin marketplace add ./dist) exige nova sessao - nao validei automaticamente, fica pra teste manual humano em uso real.
- doctor: Guia Fluxo files OK. render --check: OK 16 alvos. test_smoke: ok. Wrapper testado de raiz: .\core\bin\guia.ps1 doctor responde.

### Validacao pendente

- Nenhuma.

## [I-004] Skills do pack nao habilitadas localmente: render-skills.py nao escreve em .claude/ na raiz

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-06-01)
- **Tipo:** Issue / regressao
- **Contexto:** Causa raiz: render-skills.py emite SKILL.md em skills/generated/.claude/skills/<verbo>/ (stage de distribuicao), mas Claude Code so descobre skills em .claude/skills/ na raiz do projeto. Como o repo-mae nao tem essa pasta, os atalhos /feature, /issue, /backlog, /promote, /ready, /finish, /status, guia-fluxo nao aparecem na sessao do Claude. Sintoma confirmado neste chat: Skill issue retornou 'Unknown skill: issue' e a lista de available skills do turno nao inclui nenhum verbo do pack. Doc tambem desalinhada: CLAUDE.md afirma que as skills estao em .claude/skills/<verbo>/SKILL.md, caminho inexistente. Fix decidido com o usuario: render-skills.py passa a escrever em ambos os destinos (skills/generated/.claude/ para distribuicao + .claude/ na raiz para dogfood local). Mesmo tratamento para .agents/ (Codex/Antigravity). Atualizar CLAUDE.md/AGENTS.md/docs/reference/cli.md refletindo o duplo destino. Issue serve como ADR informal do problema; F-009 (refactor para plugin oficial) absorve a soluc�o definitiva depois.

### Arquivos modificados/criados

- `FEATURES.md`
- `scripts/render-skills.py`
- `CLAUDE.md`
- `AGENTS.md`
- `docs/reference/cli.md`
- `CHANGELOG.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- render-skills.py agora escreve em 4 destinos: skills/generated/.claude/ e skills/generated/.agents/ (stages de distribuicao) e .claude/skills/ e .agents/skills/ na raiz (ativo runtime do dogfood). Adicionados constantes ROOT_AGENT_DIR/ROOT_CLAUDE_SKILL_DIR e func target_paths() retornando lista de Path por target logico. TARGET_LABELS virou dict de listas. collect_outputs() explode cada target em N arquivos. CLAUDE.md/AGENTS.md ajustados: regra 3 amplia o read-only para os 4 destinos. docs/reference/cli.md descreve os 4 destinos no sub-comando render. CHANGELOG ganha entrada Fixed em [Unreleased].
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/render-skills.py -> renderizou 16 arquivos novos (.claude/skills/* e .agents/skills/* na raiz). python scripts/render-skills.py --check -> OK: 32 alvo(s) em sincronia com o manifest. python scripts/guia.py doctor -> Guia Fluxo files OK. Get-ChildItem .claude/skills confirma 8 pastas (guia-fluxo, backlog, feature, finish, issue, promote, ready, status).

### Validacao pendente

- Nenhuma.

## [F-010] Hook de docs no /finish para atualizar documentacao da feature ou issue

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Hook de docs no /finish para atualizar documentacao da feature ou issue

### Arquivos modificados/criados

- `FEATURES.md`
- `scripts/guia.py`
- `.guia/docs-map.yaml`
- `skills/manifest.yaml`
- `skills/generated/.agents/skills/finish/SKILL.md`
- `skills/generated/.claude/skills/finish/SKILL.md`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/reference/docs-map.md`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `docs/explanation/por-que-docs-hook.md`
- `docs/explanation/visao-geral.md`
- `docs/adr/0005-docs-hook-no-finish.md`
- `docs/adr/README.md`
- `CHANGELOG.md`
- `CLAUDE.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `README.md`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Hook de docs no /finish: guia.py le .guia/docs-map.yaml (opcional), computa candidatos via triggers (task-finished, touched, architectural-decision), e bloqueia o finish ate o agente passar --docs-touched/--docs-skip. Subcomando standalone docs-check exposto (texto e --json). docsReview gravado em tasks.json. Dogfood: .guia/docs-map.yaml deste repo lista 9 docs vivos.
- Skill /finish reescrita: ensina rodar docs-check antes, registrar com --docs-touched/--docs-skip; agent_skill e claude_skill regenerados via render-skills.py.
- Docs novos: how-to/manter-docs-atualizados.md, reference/docs-map.md, explanation/por-que-docs-hook.md, adr/0005-docs-hook-no-finish.md. ADR README, files.md, cli.md, visao-geral.md, CHANGELOG, CLAUDE.md, AGENTS.md, CONTRIBUTING.md, README.md atualizados pra refletir o novo passo.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/guia.py doctor -> Guia Fluxo files OK.
- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- python scripts/guia.py docs-check F-010 -> lista 9 candidatos corretos (FEATURES, CHANGELOG, README, cli.md, visao-geral, adr/, CLAUDE.md, AGENTS.md, CONTRIBUTING.md) com motivos task-finished/touched/architectural-decision.
- python scripts/guia.py finish F-010 --no-commit (sem flags de docs) -> bloqueia com exit 1 e imprime o painel completo. Hook funciona.

### Validacao pendente

- Nenhuma.

## [F-009] Migrar layout para plugin oficial Claude Code (A+B base) + ADR-0005

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Pesquisa arquitetural (2026-05-31) confirmou opcao A+B com alvo tri-agente (Claude principal, Codex secundario, Antigravity terciario). Esta demanda e o fundamento estrutural: (1) adicionar .claude-plugin/plugin.json na raiz com manifest oficial; (2) reorganizar a saida do render-skills.py para o layout root-level oficial (skills/, commands/, hooks/, bin/) em vez de skills/generated/.claude/...; (3) manter skills/generated/.agents/ para Codex+Antigravity via AGENTS.md+SKILL.md cross-tool; (4) preservar scripts/guia.py como motor (skills continuam thin wrappers); (5) escrever ADR-0005 documentando a decisao com links pra https://code.claude.com/docs/en/plugins e o padrao AGENTS.md (Linux Foundation). Bloqueia o restante do backlog (marketplace.json, MCP server, PreToolUse hook, compat cross-agent, consolidacao AGENTS/CLAUDE, docs Diataxis).

### Arquivos modificados/criados

- `FEATURES.md`
- `.claude-plugin/plugin.json`
- `plugin-src/manifest.yaml`
- `scripts/render-skills.py`
- `scripts/guia.py`
- `skills/guia-fluxo/SKILL.md`
- `skills/feature/SKILL.md`
- `skills/issue/SKILL.md`
- `skills/backlog/SKILL.md`
- `skills/promote/SKILL.md`
- `skills/ready/SKILL.md`
- `skills/finish/SKILL.md`
- `skills/status/SKILL.md`
- `.agents/skills/guia-fluxo/SKILL.md`
- `docs/adr/0006-plugin-oficial-claude-code.md`
- `docs/adr/README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `README.md`
- `docs/reference/cli.md`
- `docs/reference/files.md`
- `docs/explanation/visao-geral.md`
- `docs/how-to/instalar-em-outro-projeto.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.guia/docs-map.yaml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/render-check.yml`
- `.claude-plugin/marketplace.json`
- `.claude/settings.json`
- `.guia/backlog.json`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Layout oficial de plugin Claude Code: .claude-plugin/plugin.json (name=ai) na raiz expoe os 8 verbos sob namespace ai (/guia:feature, /guia:issue, etc.). Source do manifest movido de skills/manifest.yaml para plugin-src/manifest.yaml. render-skills.py reduzido de 4 destinos para 2: skills/<verbo>/SKILL.md (output do plugin Claude oficial) + .agents/skills/<verbo>/SKILL.md (cross-tool Codex+Antigravity via convencao AGENTS.md). Removidos skills/generated/ e .claude/skills/ na raiz. ADR-0006 criado documentando a decisao com tradeoffs e alternativas rejeitadas (standalone, nome longo, source em path nao-padrao, bin/ ja nesta demanda). Docs vivos atualizados: CLAUDE.md, AGENTS.md, cli.md, files.md, visao-geral.md, CHANGELOG.md, README.md, CONTRIBUTING.md, instalar-em-outro-projeto.md, SECURITY.md, PULL_REQUEST_TEMPLATE.md, render-check.yml, docs-map.yaml. scripts/guia.py: help text do subcomando render ajustado.
- Scope expandido durante validacao: alem do plugin oficial Claude Code (item 1-6 do ADR-0006), incluido marketplace local autoregistrado (item 7). Adicionados .claude-plugin/marketplace.json (catalogo name=guia-fluxo, plugin source=./) e .claude/settings.json (extraKnownMarketplaces com source directory + enabledPlugins habilitando ai@guia-fluxo). Resultado: ao abrir o repo em Claude Code (primeira vez), o user recebe prompt de trust + install e os atalhos /guia:feature, /guia:issue, etc ficam disponiveis nas sessoes futuras sem precisar de --plugin-dir manual. Absorve a demanda B-001 do backlog. ADR-0006 atualizado com item 7 da Decisao, consequencia positiva da descoberta automatica recuperada, e nota de versao minima (Claude Code 2.1.x+) nas Consequencias. CLAUDE.md, README.md, instalar-em-outro-projeto.md atualizados com as 3 vias de instalacao (dogfood/marketplace publico/copia manual). CHANGELOG.md ganhou nova entry Added sobre o marketplace local.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- python scripts/guia.py doctor -> Guia Fluxo files OK.
- python -m unittest tests.test_smoke -v -> OK, 1 teste passou. Smoke nao depende dos paths novos, mas confirma que scripts/guia.py continua intacto.
- Get-ChildItem skills, .agents/skills -Directory confirma 8 pastas em cada (guia-fluxo, backlog, feature, finish, issue, promote, ready, status). 16 SKILL.md no total.
- python -m unittest tests.test_smoke -v -> OK, 1 teste passou.
- Get-ChildItem .claude-plugin confirma 2 arquivos (marketplace.json, plugin.json). Get-ChildItem .claude confirma settings.json. Get-ChildItem skills, .agents/skills -Directory confirma 8 pastas em cada (16 SKILL.md no total).

### Validacao pendente

- Nenhuma.

## [F-008] Criar ADRs iniciais (4 decisoes fundadoras)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Em 6 meses, contribuidor novo (ou voce mesmo) abre o repo, ve uma decisao 'estranha' (script como fonte de verdade, lock por commit-message, JSON+Markdown dual, chat-title sincronizado), refaz tudo, quebra caso ja resolvido. ADR e vacina contra retrabalho. Criados em docs/adr/: README+template+4 ADRs. Linkados a partir de explanation/ (decisao canonica vs ensinamento pedagogico) e do README raiz. Estrutura segue convencao classica: NNNN-kebab.md, status (Proposta/Aceita/Substituida/Depreciada), secoes Contexto/Decisao/Consequencias/Alternativas/Links.

### Arquivos modificados/criados

- `FEATURES.md`
- `docs/adr/README.md`
- `docs/adr/template.md`
- `docs/adr/0001-script-fonte-da-verdade.md`
- `docs/adr/0002-lock-por-commit-message.md`
- `docs/adr/0003-json-maquina-markdown-humano.md`
- `docs/adr/0004-chat-title-sincronizado.md`
- `docs/README.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`
- `docs/explanation/por-que-lock.md`
- `README.md`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Criada estrutura docs/adr/ com README (indice+convencoes), template, e 4 ADRs iniciais (script fonte de verdade, lock por commit-message, JSON/Markdown dual, chat-title sincronizado). Links cruzados: docs/README.md e README.md raiz apontam para adr/; explanation/por-que-script-fonte-da-verdade.md e explanation/por-que-lock.md ganharam banner apontando o ADR como decisao canonica (explanation continua como versao pedagogica). Convencao: NNNN-kebab.md, status Proposta/Aceita/Substituida/Depreciada, secoes Contexto/Decisao/Consequencias/Alternativas/Links.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/guia.py doctor -> Guia Fluxo files OK.
- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- ls docs/adr/ confirma 6 arquivos: README.md, template.md, 0001..0004.

### Validacao pendente

- Nenhuma.

## [F-007] .editorconfig e .gitattributes para padronizar line endings cross-platform

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Sem .gitattributes, Windows commita CRLF e Mac/Linux LF: diff inteiro fantasma a cada PR. Pior: pack tem .githooks/commit-msg (shell sem extensao) - bash recusa executar com CRLF, entao o primeiro Mac que clonar quebra o hook de lock. Roadmap promete Unix em v0.3 - sem isso, regressao garantida. Solucao: (a) .editorconfig (UTF-8, LF default, 4 espacos; YAML/JSON 2; Markdown sem trim; ps1/bat CRLF; hooks LF) que padroniza editores (VS Code, JetBrains, Vim leem nativamente); (b) .gitattributes que forca eol=lf no commit/checkout por default e overrides eol=crlf para *.ps1/*.psm1/*.psd1/*.bat/*.cmd e eol=lf explicito para .githooks/* e templates/.githooks/* (cobre o commit-msg sem extensao). Caveats: arquivos ja tracked com CRLF (FEATURES.md, skills/generated/**/SKILL.md) ficam stale ate rodar git add --renormalize . em commit separado; scripts/render-skills.py grava com newline do SO (write_text sem newline=) - fix de 1 linha que fica como follow-up.

### Arquivos modificados/criados

- `FEATURES.md`
- `.editorconfig`
- `.gitattributes`
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Adicionados .editorconfig e .gitattributes na raiz. .editorconfig (UTF-8, LF default, 4 espacos; YAML/JSON/TOML em 2; Markdown sem trim_trailing_whitespace; *.ps1/*.psm1/*.psd1/*.bat/*.cmd em CRLF; .githooks/* e templates/.githooks/* em LF; Makefile com tab) padroniza editores VS Code/JetBrains/Vim. .gitattributes (* text=auto eol=lf como base; overrides eol=crlf para PowerShell e batch; eol=lf explicito para .sh/.bash/Python/YAML/JSON/TOML/INI/MD/TXT e para .githooks/* e templates/.githooks/* que cobrem commit-msg sem extensao; *.png/jpg/jpeg/gif/ico/pdf/zip/gz/tar/woff/woff2 marcados binary) garante normalizacao no commit. Validado via git check-attr: .githooks/commit-msg=lf, scripts/guia.ps1=crlf, scripts/guia.py=lf, templates/.githooks/commit-msg=lf.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/guia.py doctor => Guia Fluxo files OK. python scripts/render-skills.py --check => OK: 16 alvo(s) em sincronia com o manifest. git check-attr -a confirma rules aplicadas nos arquivos-chave.

### Validacao pendente

- Nenhuma.

## [F-006] Smoke test do fluxo basico do pack (ai init -> feature -> ready -> finish)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Sem teste automatizado, toda mudanca em guia.py ou render-skills.py e um pulo no escuro: hoje so se sabe que finish --lock ainda funciona rodando manualmente, o que e caro e ninguem faz sempre. Smoke test (engenharia eletrica: liga o aparelho, se nao soltou fumaca o primeiro check passou) cobre o caminho feliz mais comum num arquivo enxuto (~20 linhas, ~2s) e pega 80% das regressoes. Para o pack: tests/test_smoke.py cria diretorio temporario, roda em sequencia ai init / ai feature 'teste' / ai ready F-001 / ai finish F-001 e valida que .guia/tasks.json terminou com status 'Validada' no fim. Justamente porque o projeto e pequeno a barreira pra adicionar 1 teste e baixissima e ganha-se tranquilidade pra refatorar sem medo. Pendencias: (a) escolher framework (unittest da stdlib evita dependencia nova), (b) integrar no .github/workflows/ que entra via F-005 (rodar nos PRs), (c) documentar como rodar em CONTRIBUTING.md.

### Arquivos modificados/criados

- `FEATURES.md`
- `tests/test_smoke.py`
- `.guia/tasks.json`
- `.guia/current-task.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- tests/test_smoke.py adicionado: ~30 linhas, stdlib unittest (zero deps), roda init/feature/ready/finish num tempdir e valida que tasks.json terminou com status Validada. Smoke test sem framework externo.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python -m unittest tests.test_smoke -v -> OK, 1 teste passou em 1.365s.

### Validacao pendente

- Nenhuma.

## [F-005] Pasta .github/ - templates de issue/PR e workflows (lock-check, render-check)

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
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
- `.guia/tasks.json`
- `.guia/current-task.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- Criada estrutura .github/ com 5 arquivos: bug_report.md (template de issue), config.yml (bloqueia issue em branco), PULL_REQUEST_TEMPLATE.md (checklist de demanda/lock/validacao), lock-check.yml (workflow que re-checa python bin/check-lock.py ci no PR - terceira camada do protocolo de lock prometida em docs/explanation/por-que-lock.md), render-check.yml (rodam ai doctor + render-skills.py --check em mudancas que afetam skills/.ai).
- Sem hardcode de URL absoluta: nao ha git remote configurado ainda; config.yml deixa contact_links vazio e aponta para SECURITY.md (rastreado em I-003).
- Pasta .github/ entregue e validada localmente. Commit feito manualmente apos finish para incluir [unlock:adicoes-exigem-autorizacao] no message (5 arquivos novos sob .github/ disparariam o lock global), e para isolar os arquivos da demanda dos demais nao commitados no working tree (CONTRIBUTING.md, LICENSE, SECURITY.md de I-003, deletes do skills/ legados, etc.).

### Validacao feita

- YAML parseado com pyyaml para .github/workflows/{lock-check,render-check}.yml e .github/ISSUE_TEMPLATE/config.yml -> OK.
- Simulado python bin/check-lock.py ci com features de teste: bloqueia add sem [unlock:...] (exit 1, mensagem com instrucao); passa com [unlock:adicoes-exigem-autorizacao] no msg (exit 0).
- python scripts/guia.py doctor -> Guia Fluxo files OK; python scripts/render-skills.py --check -> 16 alvos em sincronia.

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
- `.guia/current-task.json`
- `.guia/tasks.json`
- `docs/README.md`
- `docs/explanation/por-que-lock.md`
- `docs/explanation/por-que-script-fonte-da-verdade.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Adicionados os 5 arquivos de governanca + LICENSE MIT (entregue na resposta anterior) + atualizacao do README com secao 'Contribuindo' e troca de 'A definir' por link para MIT.
- LICENSE: MIT padrao, copyright 2026 Paulo Marcos.
- CONTRIBUTING.md: pre-requisitos, setup, fluxo via guia-fluxo (issue/feature -> ready -> finish), edicao de skills via manifest + render, padrao de commit (feature:/issue:/chore: + [unlock:<id>]), PR.
- SECURITY.md: canal privado paulolinhodboa@gmail.com + GitHub Security Advisory, prazos (5 dias uteis para acuse, 10 para avaliacao), escopo (bypass de lock/render, corrupcao de .ai, injecao em CLI).
- CODE_OF_CONDUCT.md: Contributor Covenant v2.1 traduzido, contato paulolinhodboa@gmail.com.
- AGENTS.md: brief generico (Codex/Cursor/Antigravity) - regras nao-negociaveis (script e fonte de verdade, nao editar skills/generated, respeitar lock), fluxo padrao, comandos uteis, anti-padroes.
- CLAUDE.md: brief especifico Claude Code - skills locais, PowerShell, regras + verificacao antes de entregar, anti-padroes.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- .\\scripts\\guia.ps1 doctor => Guia Fluxo files OK.
- python scripts/render-skills.py --check => OK, 16 alvos em sincronia com o manifest

### Validacao pendente

- Nenhuma.

## [F-004] Dogfood do proprio pack: ai init + githooks + features/

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Pack ensina .guia/ e FEATURES.md mas o repo nao usa: process.json e backlog.json faltam (ai doctor falha), .githooks/ nao instalado, features/registry.yaml ausente. Sem self-use o repo perde credibilidade e o pack nao recebe feedback de seu primeiro usuario. Instalar bootstrap completo aqui mesmo (modelo A: commitar JSON state, gitignore reports/chat-title).

### Arquivos modificados/criados

- `FEATURES.md`
- `.guia/process.json`
- `.guia/backlog.json`
- `.gitignore`
- `.githooks/commit-msg`
- `features/registry.yaml`
- `features/lock-ignore.txt`
- `.guia/tasks.json`
- `.guia/current-task.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- ai init criou .guia/process.json e .guia/backlog.json (doctor agora passa).
- Templates copiados para raiz: .githooks/commit-msg, features/registry.yaml, features/lock-ignore.txt.
- .gitignore exclui .guia/chat-title.txt e .guia/reports/ (volateis); demais JSONs do .guia/ ficam versionados para cross-clone.
- Pack agora dogfooda a si mesmo: bootstrap completo (ai init + .githooks/ + features/) instalado e versionado. Proximo melhoria entra como F-005/I-003 via ai feature/issue, fechando o ciclo.

### Validacao feita

- python scripts/guia.py doctor -> Guia Fluxo files OK.
- python scripts/guia.py render --check -> OK: 16 alvo(s) em sincronia.
- python bin/check-lock.py list -> lista a trava 'adicoes-exigem-autorizacao' do template.

### Validacao pendente

- Nenhuma.

## [F-003] Diferenciar descriptions das skills para evitar trigger collision

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** As 7 shims (feature, issue, backlog, ready, finish, status, promote) e a guia-fluxo tem descriptions parecidas. O agente fica confuso sobre qual disparar. Cada description precisa de marcadores unicos no inicio (gatilho explicito, escopo, quando NAO usar) para que o roteador escolha a skill certa sem ambiguidade.

### Arquivos modificados/criados

- `FEATURES.md`
- `skills/manifest.yaml`
- `skills/generated/.claude/skills/guia-fluxo/SKILL.md`
- `skills/generated/.claude/skills/feature/SKILL.md`
- `skills/generated/.claude/skills/issue/SKILL.md`
- `skills/generated/.claude/skills/backlog/SKILL.md`
- `skills/generated/.claude/skills/promote/SKILL.md`
- `skills/generated/.claude/skills/ready/SKILL.md`
- `skills/generated/.claude/skills/finish/SKILL.md`
- `skills/generated/.claude/skills/status/SKILL.md`
- `skills/generated/.agents/skills/guia-fluxo/SKILL.md`
- `skills/generated/.agents/skills/feature/SKILL.md`
- `skills/generated/.agents/skills/issue/SKILL.md`
- `skills/generated/.agents/skills/backlog/SKILL.md`
- `skills/generated/.agents/skills/promote/SKILL.md`
- `skills/generated/.agents/skills/ready/SKILL.md`
- `skills/generated/.agents/skills/finish/SKILL.md`
- `skills/generated/.agents/skills/status/SKILL.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Reescritas as 8 descriptions (guia-fluxo + 7 shims) com marcadores unicos em CAPS (PRIMARY TRIGGER, REFERENCE/BACKGROUND, READ-ONLY, DEFER-AND-PARK, EVALUATE-AND-CONVERT, HANDOFF, CLOSE) e clausula 'Do NOT use for: ... (use )' para eliminar trigger collision entre as skills do pack.

### Validacao feita

- python scripts/render-skills.py --check => OK, 16 alvos em sincronia com o manifest

### Validacao pendente

- Nenhuma.

## [F-002] Enxugar README seguindo Standard Readme

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Feature
- **Contexto:** README tinha ~120 linhas misturando intro, layout, paridade entre agentes, copy table de instalacao e roadmap. Padrao Standard Readme manda responder em ordem com cortes (o que e, por que, instalar, usar, links para o resto). Mover detalhe para docs/INSTALL.md e docs/ROADMAP.md; manter README como porta de entrada.

### Arquivos modificados/criados

- `FEATURES.md`
- `README.md`
- `docs/INSTALL.md`
- `docs/ROADMAP.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- README reduzido de ~120 para 53 linhas na ordem Standard Readme (o que e -> por que -> instalar -> usar -> links). docs/INSTALL.md absorveu a copy table e bootstrap; docs/ROADMAP.md absorveu as 4 entradas de roadmap.
- Commit feito manualmente apos finish para nao misturar com arquivos do F-001 ainda nao commitados (skills/agents/* e skills/claude/* deletados, FEATURES.md de F-001 ja estava em e053a84).

### Validacao feita

- Inspecao visual do README e verificacao de que todos os links da secao Documentacao apontam para arquivos existentes (ls docs/).

### Validacao pendente

- Nenhuma.

## [I-002] Diátaxis para docs/: confirmar escopo vs README/CHANGELOG e implementar

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
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
- `.guia/current-task.json`
- `.guia/tasks.json`

### O que foi feito

- Demanda criada via guia-fluxo.
- docs/ reorganizada via Diataxis: 1 tutorial, 9 how-tos, 6 references, 5 explanations. Removidos AI_PROCESS/PROTOCOL/HOOKS/INSTALL (conteudo migrado sem perda). README, CHANGELOG e comments do registry atualizados.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- ls docs/ confirma estrutura; grep por docs/AI_PROCESS|PROTOCOL|HOOKS|INSTALL retorna so historico imutavel (CHANGELOG, FEATURES.md, .guia/tasks.json) e a explanation por-que-diataxis.md (referencia intencional ao antes)

### Validacao pendente

- Nenhuma.

## [F-001] Reestruturar skills/ com generated/ e deprecar .claude/commands

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
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

- Demanda criada via guia-fluxo.
- Manifest: claude_command convertido em claude_skill em todos os verbos; validate (deprecated) removido. Render: alvos passam a sair em skills/generated/.agents/skills/ e skills/generated/.claude/skills/, target claude_command removido. Apagadas as arvores skills/agents/ e skills/claude/. README/AI_PROCESS/CHANGELOG atualizados refletindo a nova estrutura mirror-the-destination.
- Demanda finalizada via guia-fluxo.

### Validacao feita

- python scripts/render-skills.py (16/16 alvos gerados), python scripts/render-skills.py --check (OK)

### Validacao pendente

- Nenhuma.

## [I-001] Paridade de skills/comandos entre Claude, Codex e Antigravity - usar fonte unica

- **Status:** Validada
- **Origem:** Guia Fluxo (2026-05-31)
- **Tipo:** Issue / regressao
- **Contexto:** Paridade de skills/comandos entre Claude, Codex e Antigravity - usar fonte unica

### Arquivos modificados/criados

- `FEATURES.md`
- `skills/manifest.yaml`
- `scripts/render-skills.py`
- `scripts/guia.py`
- `README.md`
- `skills/agents/guia-fluxo/SKILL.md`
- `skills/agents/promote/SKILL.md`

### O que foi feito

- Demanda criada via guia-fluxo.
- Manifest YAML unico em skills/manifest.yaml como fonte de verdade dos verbos por agente.
- Renderer scripts/render-skills.py gera .agents/skills, .claude/commands e .claude/skills a partir do manifest.
- Subcomando 'ai render' (com --check e --verb) wrappa o renderer mantendo UX via guia.ps1.
- README documenta paridade: Codex+Antigravity compartilham .agents/skills; Claude usa commands+skills; edicao passa pelo manifest.
- guia-fluxo SKILL agora cita Antigravity explicitamente e referencia o workflow do manifest.

### Validacao feita

- ai render --check -> OK: 17 alvo(s) em sincronia com o manifest.
- ai render (idempotente): segunda execucao nao grava nada.

### Validacao pendente

- Nenhuma.

