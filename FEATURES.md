# Features e Issues

---

## [F-019] Render polish: --clean, --output-dir, frontmatter extras, shared_body explicito

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 4.Q3 (--clean real para apagar orfaos), 4.5 (--output-dir configuravel), 4.11 (frontmatter extras como allowed-tools/model), 1.5 (shared_body explicito via campo dedicado em vez de body_file duplicado). Tudo no core/build/render-skills.py mantendo backward compat.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `tests/test_render_polish.py`
- `CHANGELOG.md`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Render-skills ganha 4 capacidades: (1) --clean apaga orfaos + diretorios vazios apos render (com filtro para __pycache__/.pytest_cache); (2) --output-dir reaponta DIST_DIR via _retarget_dist em runtime, --check tambem respeita; (3) frontmatter extras: verbs.X.frontmatter aceita allowed-tools/model com sanity check (name/description reservados); (4) shared_body explicito: verbs.X.shared_body aponta body unico aplicado a TODOS targets sem body_file proprio.
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest discover -s tests -> Ran 96 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvos
- python core/build/render-skills.py --output-dir <tmp> -> 41 arquivos gerados em pasta custom
- --check-orphans antes listava 18 .pyc; agora ignora __pycache__ e diz 'OK: nenhum orfao'

### Validacao pendente

- Nenhuma.

## [F-018] Hardening: doctor estendido, check-lock info/edit/history/--json, dedup hook commit-msg

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achados 2.10 (doctor so checa 4 arquivos), 5.Q2 (check-lock sem info/edit/history), 5.Q3 (sem flag --json) e 6.Q1 (core/hooks/commit-msg e core/templates/.githooks/commit-msg sao byte-identicos sem deduplicacao). Esta feature implementa: (1) doctor estende verificacoes (manifest YAML carregavel, PyYAML disponivel, git no PATH, render --check OK, dist/ alinhado, lock_api importavel); (2) check-lock ganha 3 subcomandos novos (info <id>, edit <id> --add-file ..., history <id>); (3) check-lock list/check/audit/info aceitam --json; (4) core/templates/.githooks/commit-msg vira copia gerada pelo renderer a partir de core/hooks/commit-msg (fonte unica).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_cli_lifecycle.py`
- `core/src/ai.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `core/build/render-skills.py`
- `tests/test_check_lock_info_edit_history.py`
- `tests/test_doctor_extended.py`
- `CHANGELOG.md`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`
- `dist/bin/_cli_lifecycle.py`
- `dist/bin/ai.py`
- `dist/bin/lock_api.py`

### O que foi feito

- Demanda criada via ai-process.
- doctor estendido: checa manifest YAML carregavel, PyYAML, git no PATH, render --check, dist/bin/ai.py, lock_api importavel. Flags --strict (warning vira erro) e --skip-render (CI rapido). Detecta layout consumer (sem core/) via _is_dev_repo e degrada para modo 'lite' que so checa .ai/ + git.
- check-lock ganhou 3 subcomandos: info <id> (detalhes), edit <id> --add-file/--remove-file/--description (preserva id+locked_at), history <id> (git log filtrado por [unlock:<id>]).
- Flag --json adicionada em list/check/info/audit/history do check-lock. Payload coerente com schema (count, locks, ok, blocked, etc.).
- lock_api ganhou get_lock(id) e edit_lock(id, add/remove/description) com excecoes proprias (LockNotFound, LockIgnoredPath, LockOutsideRepo) reutilizadas pelo CLI.
- Dedup commit-msg: core/templates/.githooks/commit-msg apagado. Renderer ganhou PROMOTED_TEMPLATES que copia core/hooks/commit-msg direto para dist/templates/.githooks/commit-msg. Fonte unica em core/hooks/.
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest discover -s tests -> Ran 90 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvo(s)
- .\core\bin\ai.ps1 doctor -> AI process files OK
- check-lock info adicoes-exigem-autorizacao -> detalhes do lock global
- check-lock history adicoes-exigem-autorizacao -> 8 commits encontrados (todos os com unlock no historico)

### Validacao pendente

- Nenhuma.

## [F-017] Subcomandos tasks list/show/filter para navegacao do .ai/tasks.json

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 achado 2.11: o CLI hoje so tem 'status' (uma task por vez via current ou ID). Falta forma rapida de listar tudo, filtrar por status/kind, e ver detalhe de uma task arbitraria sem mexer em current. Proposta: subcomando 'tasks' com 'list', 'show <ID>', 'filter --status X --kind Y --limit N'. Saida texto humana + flag --json para consumo por agente. Reaproveita _tasks.find_task, recent_task_ids; adiciona _tasks.list_tasks(filter) e _tasks.format_task_line.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/src/_tasks.py`
- `core/src/_cli_tasks.py`
- `core/src/ai.py`
- `tests/test_tasks_list.py`
- `CHANGELOG.md`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`
- `dist/bin/_tasks.py`
- `dist/bin/ai.py`

### O que foi feito

- Demanda criada via ai-process.
- Subcomando 'tasks' adicionado com 3 acoes: list/show/filter. list aceita --limit N; show <ID> retorna exit 1 se nao encontra; filter combina --status/--kind/--limit. Todos suportam --json. Helpers: _tasks.list_tasks(status,kind,limit) e _tasks.format_task_line(task). Subcomando registrado em ai.py.build_parser usando STATUS_* e KIND_* de _constants (sem strings magicas).
- Tests novos em test_tasks_list.py: 8 casos (3 list, 2 show, 3 filter) exercitando sandbox completo com init+feature+issue+ready. Total da suite: 77 testes.
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest discover -s tests -> Ran 77 tests, OK
- python core/build/render-skills.py --check -> OK 41 alvo(s)
- .\core\bin\ai.ps1 tasks list --limit 5 -> lista corretamente as 5 mais recentes
- .\core\bin\ai.ps1 tasks show F-016 --json -> retorna task completa em JSON

### Validacao pendente

- Nenhuma.

## [F-016] Layout B do manifest: index YAML + bodies markdown em core/manifest/bodies/

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 Etapa 1 Q2 (aprovada): migrar core/manifest/manifest.yaml (arquivo unico 422 linhas) para layout B. Index YAML curto declara verbos, descriptions e referencia body_file/shared_body. Bodies viram arquivos markdown puros em core/manifest/bodies/<verb>.<target>.md. Renderer atualizado para resolver body_file (le do disco), shared_body (uma vez, reusa). Deliverable: manifest.yaml ~80 linhas + 14 bodies markdown + renderer estendido + smoke tests do schema novo. Saida SKILL.md em dist/ permanece byte-identica.

### Arquivos modificados/criados

- `FEATURES.md`
- `core/manifest/manifest.yaml`
- `core/manifest/bodies/ai-process.agent.md`
- `core/manifest/bodies/ai-process.claude.md`
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
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Layout B implementado: manifest.yaml passa de 422 linhas (bodies inline) para ~80 linhas (index com body_file:). 16 bodies extraidos como markdown puro em core/manifest/bodies/<verb>.<target>.md. Schema v2: body_file aponta path relativo a core/manifest/, renderer valida existencia + recusa path traversal + cacheia leituras (shared_body trivial). Backward compat com body inline v1 mantida. Saida dist/ byte-identica - confirmado por --check 40 alvos.
- Tests: 4 novos casos em test_manifest_layout_b.py validam schema (version 2, body_file presente, files existem, sem orfaos em bodies/). Total da suite: 69 testes.
- Demanda finalizada via ai-process.

### Validacao feita

- python core/build/render-skills.py --check -> OK: 40 alvo(s) em sincronia
- python -m unittest discover -s tests -> Ran 69 tests in 12.5s, OK
- .\core\bin\ai.ps1 doctor -> AI process files OK

### Validacao pendente

- Nenhuma.

## [I-005] Bugs e melhorias do CLI/check-lock identificados na auditoria F-014

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
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
- `.ai/backlog.json`

### O que foi feito

- Demanda criada via ai-process.
- Corrigidos no refactor F-015: 2.1 cleanup_task_worktree chamado uma vez so; 2.2 cmd_promote constroi task+worktree antes de mutar backlog; 2.4 _commit.commit_task normaliza paths via _paths.normalize_path; 2.5 find_task_or_current sugere recent_task_ids; 2.9 cleanup pula quando --no-commit; 2.12 has_git + MSG_GIT_NOT_FOUND em git_ops; 2.13 git_branch_exists pre-check em attach_worktree; 2.Q2 cmd_validate imprime warning de deprecacao; 5.3 cmd_audit pre-checa .git/; 5.10 cmd_lock aceita --allow-missing; 5.14 unlocked_ids exige MOTIVO_RE; 5.19 add_lock valida path traversal via _path_inside_repo; 5.2 _load_lock_ignore_cached via lru_cache.
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest discover -s tests -> 63 testes OK
- .\core\bin\ai.ps1 doctor -> OK
- python core\build\render-skills.py --check -> OK 40 alvos

### Validacao pendente

- Nenhuma.

## [F-015] Refactor SOLID/Clean Arch do core (constantes + lock_api + split modular)

- **Status:** Validada
- **Origem:** AI process (2026-06-03)
- **Tipo:** Feature
- **Contexto:** F-014 etapa 8 cluster A+B+C: centralizar strings/paths em _constants, extrair lock_api importavel (remove duplicacao 2.Q3+5.Q1, corrige bug latente lock_task_files), decompor core/src/ai.py em domain/infrastructure/cli mantendo dist/bin/ standalone via renderer que copia pacote inteiro. SOLID: SRP por modulo, OCP nos comandos via dispatch table, DIP via injecao de filesystem nos services.

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
- `core/src/ai.py`
- `core/lock/lock_api.py`
- `core/lock/check-lock.py`
- `core/build/render-skills.py`
- `core/bin/ai`
- `core/bin/ai.ps1`
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
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`
- `CHANGELOG.md`
- `dist/.agents/skills/ai-finish/SKILL.md`
- `dist/.agents/skills/ai-promote/SKILL.md`
- `dist/bin/ai.ps1`
- `dist/bin/ai.py`
- `dist/skills/feature/SKILL.md`
- `dist/skills/issue/SKILL.md`
- `dist/skills/promote/SKILL.md`
- `docs/adr/README.md`
- `docs/adr/0007-arquitetura-modular-core-src.md`
- `docs/auditorias/F-014-validacao.md`

### O que foi feito

- Demanda criada via ai-process.
- Refactor SOLID/Clean Architecture/DDD do core: 17 novos modulos sob core/src/_*.py (constants, state, paths, clock, git_ops, tasks, features_md, process_config, docs_hook, locks, worktree, commit, reports, validation_runner, cli_lifecycle, cli_creation, cli_meta) + lock_api em core/lock/. ai.py reduzido de 965 para ~205 linhas (so wiring + parser). check-lock.py reduzido a CLI fino sobre lock_api. render-skills.py hardened com dataclass Output, --check-orphans, abortar em marker ausente, validacao YAML. Wrappers: ai.ps1 com Resolve-Python em camadas + validacao versao 3.10+ + diagnostico rico + glob de Python3*; core/bin/ai POSIX simetrico. Bodies do manifest alinhados ao CLI (--context, worktree branch codex/<slug>, rodape ai-process em promote/finish).
- Achados implementados: A (constants), B (lock_api), C (split modular), D (1,2,4,5,9,12,13,Q2), E (Q1,Q2,4,5,6,8), F (3,6,Q2,Q3,12,17), G (1,3,8), H (3,10,14,19,2). Total ~28 dos 90 achados endereco direto, mais alguns indiretos por centralizacao.
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest discover -s tests: 63 testes em 6.3s, OK
- .\core\bin\ai.ps1 doctor: AI process files OK
- python core\build\render-skills.py --check: OK 40 alvos em sincronia

### Validacao pendente

- Nenhuma.

## [F-014] Auditoria estruturada de core/ para mapear features, issues e backlog

- **Status:** Em desenvolvimento
- **Origem:** AI process (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Walkthrough em 7 etapas (manifest, ai.py, ai.ps1, render-skills.py, check-lock.py, hooks, templates) de cada arquivo em core/. Para cada arquivo: funcao atual, riscos, melhorias, possiveis adicoes. Saida: lista de candidatos classificados como feature/issue/backlog para abertura em lote ao final. Inclui doc de acompanhamento em docs/explanation/ para rastrear progresso entre sessoes e fora do chat.

### Arquivos modificados/criados

- `FEATURES.md`

### O que foi feito

- Demanda criada via ai-process.

### Validacao feita

- Nenhuma.

### Validacao pendente

- Executar implementacao e validacoes.


## [F-013] B-008 passos 3+4: install.ps1/install.sh + templates em dist/ + smoke do consumer

- **Status:** Validada
- **Origem:** AI process (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Continuacao direta de F-012 (que entregou passos 1+2 de B-008: renderer com prefixo ai- + dist/bin/ standalone). Faltam: (a) install.ps1 + install.sh na raiz do repo-mae que copia dist/.claude-plugin/ + dist/skills/ + dist/bin/ -> consumer/.ai-process/, dist/.agents/skills/ -> consumer/.agents/skills/, e dispara 'ai init' pra semear .ai/ + FEATURES.md. (b) Templates em dist/templates/ (.githooks/commit-msg, features/registry.yaml, features/lock-ignore.txt) que o instalador opcionalmente copia. (c) Atualizar docs/how-to/instalar-em-outro-projeto.md com a rota install.ps1. (d) Smoke test estendido pra simular install num tempdir + 'ai doctor' do .ai-process/bin/ e validar layout final. Decisao tecnica: install.ps1 sera idempotente (re-rodar sobrescreve dist/* mas preserva .ai/ existente) e --dry-run para previsualizar. Dogfood do repo-mae nao e tocado nesta feature - fica como follow-up separado (criar symlink .agents -> dist/.agents no proprio repo ou install loopback).

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
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`
- `CHANGELOG.md`
- `docs/explanation/visao-geral.md`

### O que foi feito

- Demanda criada via ai-process.
- Renderer estendido para empacotar templates em dist/templates/: copia core/templates/.githooks/commit-msg, core/templates/features/registry.yaml e core/templates/features/lock-ignore.txt mantendo layout 1:1. Total de alvos cobertos passou de 19 para 22.
- install.ps1 na raiz: copia idempotente de dist/* para o consumer (.ai-process/ recebe .claude-plugin/+skills/+bin/; .agents/skills/ vai pra raiz do consumer; templates vao pra .githooks/ e features/ preservando customizacao - use -Force pra sobrescrever). Roda 'python .ai-process/bin/ai.py init' ao final. Flags -Target, -DryRun, -Force, -SkipInit. Validado dry-run e real install em tempdir.
- install.sh paridade comportamental: mesmas flags em formato POSIX (--target, --dry-run, --force, --skip-init), mesmo mapa de copia via cp -R, chmod +x automatico em .githooks/commit-msg e .ai-process/bin/ai.
- tests/test_install.py: 3 casos cobrindo (a) layout completo apos install + frontmatter ai-feature/ai-process + doctor exit 0 do consumer; (b) shim POSIX LF puro (anti-regressao); (c) wrapper ps1 aponta pra ai.py local (nao ..\\src\\ai.py). Roda cross-platform porque replica logica do installer em Python puro.
- docs/how-to/instalar-em-outro-projeto.md reescrito: TL;DR com install.ps1/install.sh, layout final, tabela de flags, secao 'idempotencia', upgrade flow, desinstalar, mapa por agente, fallback copia-manual.
- Demanda finalizada via ai-process.

### Validacao feita

- python core/build/render-skills.py --check -> OK 22 alvo(s).
- python -m unittest tests.test_smoke tests.test_install -v -> Ran 4 tests, OK (smoke base + 3 novos do install).
- .\core\bin\ai.ps1 doctor -> AI process files OK.
- install.ps1 -DryRun em tempdir: lista as 9 operacoes de copia + init sem escrever; install real em tempdir: cria todos os 28 arquivos esperados; 'python .ai-process/bin/ai.py doctor' do consumer retorna AI process files OK.
- test_install valida: name: ai-feature no frontmatter cross-tool, name: ai-process sem duplo prefixo, sem skills 'feature' (sem prefixo) em .agents/skills/, shim POSIX e LF puro.

### Validacao pendente

- Nenhuma.

## [F-012] B-008: Passo 2 - Layout .ai-process/ no consumidor com bin/ e prefixo ai- nas skills cross-tool

- **Status:** Validada
- **Origem:** Backlog B-008 (2026-06-02)
- **Tipo:** Feature
- **Contexto:** Backlog B-008: Migrar projeto consumidor pro layout: 3 pastas (.agents/, .claude/, .ai-process/) + raiz (.ai/, FEATURES.md, opcional features/). Especifico: (a) plugin Claude inteiro dentro de .ai-process/ com .claude-plugin/, skills/ (nomes curtos feature, issue, etc.) e bin/ (motor ai/ai.ps1 que vira PATH automaticamente segundo doc Anthropic - feature ja existente). (b) Codex/Antigravity em .agents/skills/ com prefixo ai- nos nomes (ai-feature, ai-issue, etc.) pra evitar colisao - decisao confirmada com user em F-009. (c) Renderer adaptado pra gerar 2 outputs com nomes diferentes. (d) instalador install.ps1 + install.sh que copia dist/ pra .ai-process/ no consumidor + inicializa .ai/. Depende de B-007 (Passo 1).

### Arquivos modificados/criados

- `FEATURES.md`
- `core/build/render-skills.py`
- `dist/.agents/skills/ai-process/SKILL.md`
- `dist/.agents/skills/ai-feature/SKILL.md`
- `dist/.agents/skills/ai-issue/SKILL.md`
- `dist/.agents/skills/ai-backlog/SKILL.md`
- `dist/.agents/skills/ai-promote/SKILL.md`
- `dist/.agents/skills/ai-ready/SKILL.md`
- `dist/.agents/skills/ai-finish/SKILL.md`
- `dist/.agents/skills/ai-status/SKILL.md`
- `dist/bin/ai.py`
- `dist/bin/ai.ps1`
- `dist/bin/ai`
- `CHANGELOG.md`
- `docs/explanation/visao-geral.md`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Backlog promovido via ai-process.
- Avaliacao IA: Feature: nova capacidade (gerador estendido + instalador + layout consumer). F-011 entregou core/+dist/ (lado dev); B-008 fecha lado consumer (.ai-process/+.agents/skills com prefixo ai-+install.ps1/.sh). Acionavel - F-009 ja confirmou prefixo ai-, dependencia B-007 entregue, deliverables claros.
- Renderer estendido (core/build/render-skills.py) com 2 mudancas: (1) prefixo ai- aplicado no nome do diretorio E no frontmatter name: dos arquivos .agents/skills/ai-<verb>/SKILL.md cross-tool (Codex+Antigravity); excecao para verbo ai-process que ja carrega o prefixo (helper agent_skill_name). Output Claude (dist/skills/<verb>/) inalterado pois namespace ai: do plugin ja qualifica os atalhos como /ai:feature etc. (2) Renderer agora copia core/src/ai.py -> dist/bin/ai.py (motor) e core/bin/ai.ps1 -> dist/bin/ai.ps1 (com path adaptado via _adapt_wrapper_for_plugin: ..\src\ai.py reescrito para ai.py), e gera shim POSIX dist/bin/ai. Total de alvos cobertos por --check passou de 16 para 19.
- Fix de newline (F-007 follow-up): write_text agora usa newline="\n" para evitar traducao automatica de \n para CRLF no Windows. Critico para o shim POSIX (bash quebra com CRLF: bash\r: not found) e coerente com normalizacao do .gitattributes (eol=lf default; *.ps1 eol=crlf re-aplicado no checkout).
- Docs: CHANGELOG.md ganhou entry Unreleased/Changed descrevendo F-012; docs/explanation/visao-geral.md atualizada (dist/ inclui bin/, .agents/skills/ai-<verb>, item 5 do roadmap marca passos 1+2 entregues e installer pendente).
- Demanda finalizada via ai-process.

### Validacao feita

- python core/build/render-skills.py --check -> OK: 19 alvo(s) em sincronia com o manifest.
- python -m unittest tests.test_smoke -v -> Ran 1 test in 1.057s, OK.
- .\core\bin\ai.ps1 doctor -> AI process files OK.
- .\dist\bin\ai.ps1 doctor -> AI process files OK (wrapper standalone valida que rewriting do path ai.py funciona).
- Bytes do shim POSIX dist/bin/ai: LF puro (verificado via [System.IO.File]::ReadAllBytes).
- Frontmatter inspecionado: dist/.agents/skills/ai-feature/SKILL.md tem 'name: ai-feature'; dist/.agents/skills/ai-process/SKILL.md tem 'name: ai-process' (sem duplo prefixo); dist/skills/feature/SKILL.md tem 'name: feature' (sem prefixo).

### Validacao pendente

- Nenhuma.

## [F-011] B-007: Passo 1 - Reorganizar repo do pack em core/ (dev) + dist/ (buildado)

- **Status:** Validada
- **Origem:** Backlog B-007 (2026-06-01)
- **Tipo:** Feature
- **Contexto:** Backlog B-007: Refactor interno do repo-mae: mover scripts/, plugin-src/, bin/, .githooks/, templates/ pra dentro de core/ (com subpastas src/, manifest/, build/, lock/, hooks/, templates/). Criar dist/ como saida buildada que espelha o layout do consumidor. Nao muda nada no projeto consumidor ainda - continua copia manual. Beneficio: limpa o repo-mae, separa fabrica de produto, prepara terreno pro Passo 2. Estimativa: refactor amplo, mexe em paths em todas as docs/CI/wrappers/testes.

### Arquivos modificados/criados

- `FEATURES.md`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/docs-map.yaml`
- `.ai/tasks.json`
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
- `core/src/ai.py`
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
- `scripts/ai.ps1`
- `tests/test_smoke.py`
- `core/bin/ai.ps1`
- `docs/how-to/manter-docs-atualizados.md`
- `docs/how-to/promover-backlog.md`
- `docs/adr/0006-plugin-oficial-claude-code.md`

### O que foi feito

- Backlog promovido via ai-process.
- Avaliacao IA: Refactor estrutural amplo: mover scripts/, plugin-src/, .githooks/, templates/, bin/ para core/{src,manifest,build,lock,hooks,templates} e criar dist/ como saida buildada espelhando o layout do consumidor. Separa fabrica de produto, prepara B-008/B-009. Acionavel - destino e origem claros no contexto.
- Repo-mae reorganizado em core/ (src, build, manifest, lock, hooks, templates) + dist/ (.claude-plugin, skills, .agents/skills). Self-dogfood preservado: .claude/settings.json aponta marketplace pra ./dist, marketplace.json plugin source = ../, git core.hooksPath = core/hooks. Wrapper scripts/ai.ps1 mantido e roteia pra core/src/ai.py. Render-skills.py adaptado, CI atualizada, smoke test atualizado, todos docs com paths novos. ADRs 0001 e 0006 com nota de atualizacao por F-011.
- Ajuste adicional pos-review: ai.ps1 movido de scripts/ pra core/bin/ (cumpre B-007 estritamente). Pasta scripts/ removida. Wrapper atualizado pra resolver core/src/ai.py via ..\src\ai.py e .venv via ..\..\.venv. Todas as referencias em docs/manifest/settings substituidas: .\scripts\ai.ps1 -> .\core\bin\ai.ps1 e scripts/ai.ps1 -> core/bin/ai.ps1.
- F-011 entregue. Refactor estrutural concluido: core/ (src, bin, build, manifest, lock, hooks, templates) + dist/ (.claude-plugin, skills, .agents/skills). scripts/ removida. ai.ps1 final em core/bin/ai.ps1. Wrapper testado, smoke test passa, render --check passa, doctor passa. Docs sincronizadas com novos paths (3 ADRs + 6 explanation/reference + 7 how-to + 1 tutorial + CHANGELOG + briefings + raiz). Limitacao: reinstall do plugin Claude (/plugin marketplace add ./dist) precisa de sessao nova - fica pra teste manual. Commit deixado para passo separado por causa do lock global adicoes-exigem-autorizacao.

### Validacao feita

- doctor: AI process files OK. render --check: OK 16 alvo(s) em sincronia. tests/test_smoke.py: ok (Ran 1 test in 0.857s). docs-check F-011: lista 10 candidatos, todos ja atualizados nesta entrega. core.hooksPath = core/hooks.
- Limitacao conhecida: reinstall do plugin no Claude Code (/plugin marketplace add ./dist) exige nova sessao - nao validei automaticamente, fica pra teste manual humano em uso real.
- doctor: AI process files OK. render --check: OK 16 alvos. test_smoke: ok. Wrapper testado de raiz: .\core\bin\ai.ps1 doctor responde.

### Validacao pendente

- Nenhuma.

## [I-004] Skills do pack nao habilitadas localmente: render-skills.py nao escreve em .claude/ na raiz

- **Status:** Validada
- **Origem:** AI process (2026-06-01)
- **Tipo:** Issue / regressao
- **Contexto:** Causa raiz: render-skills.py emite SKILL.md em skills/generated/.claude/skills/<verbo>/ (stage de distribuicao), mas Claude Code so descobre skills em .claude/skills/ na raiz do projeto. Como o repo-mae nao tem essa pasta, os atalhos /feature, /issue, /backlog, /promote, /ready, /finish, /status, ai-process nao aparecem na sessao do Claude. Sintoma confirmado neste chat: Skill issue retornou 'Unknown skill: issue' e a lista de available skills do turno nao inclui nenhum verbo do pack. Doc tambem desalinhada: CLAUDE.md afirma que as skills estao em .claude/skills/<verbo>/SKILL.md, caminho inexistente. Fix decidido com o usuario: render-skills.py passa a escrever em ambos os destinos (skills/generated/.claude/ para distribuicao + .claude/ na raiz para dogfood local). Mesmo tratamento para .agents/ (Codex/Antigravity). Atualizar CLAUDE.md/AGENTS.md/docs/reference/cli.md refletindo o duplo destino. Issue serve como ADR informal do problema; F-009 (refactor para plugin oficial) absorve a soluc�o definitiva depois.

### Arquivos modificados/criados

- `FEATURES.md`
- `scripts/render-skills.py`
- `CLAUDE.md`
- `AGENTS.md`
- `docs/reference/cli.md`
- `CHANGELOG.md`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- render-skills.py agora escreve em 4 destinos: skills/generated/.claude/ e skills/generated/.agents/ (stages de distribuicao) e .claude/skills/ e .agents/skills/ na raiz (ativo runtime do dogfood). Adicionados constantes ROOT_AGENT_DIR/ROOT_CLAUDE_SKILL_DIR e func target_paths() retornando lista de Path por target logico. TARGET_LABELS virou dict de listas. collect_outputs() explode cada target em N arquivos. CLAUDE.md/AGENTS.md ajustados: regra 3 amplia o read-only para os 4 destinos. docs/reference/cli.md descreve os 4 destinos no sub-comando render. CHANGELOG ganha entrada Fixed em [Unreleased].
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/render-skills.py -> renderizou 16 arquivos novos (.claude/skills/* e .agents/skills/* na raiz). python scripts/render-skills.py --check -> OK: 32 alvo(s) em sincronia com o manifest. python scripts/ai.py doctor -> AI process files OK. Get-ChildItem .claude/skills confirma 8 pastas (ai-process, backlog, feature, finish, issue, promote, ready, status).

### Validacao pendente

- Nenhuma.

## [F-010] Hook de docs no /finish para atualizar documentacao da feature ou issue

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Hook de docs no /finish para atualizar documentacao da feature ou issue

### Arquivos modificados/criados

- `FEATURES.md`
- `scripts/ai.py`
- `.ai/docs-map.yaml`
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
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Hook de docs no /finish: ai.py le .ai/docs-map.yaml (opcional), computa candidatos via triggers (task-finished, touched, architectural-decision), e bloqueia o finish ate o agente passar --docs-touched/--docs-skip. Subcomando standalone docs-check exposto (texto e --json). docsReview gravado em tasks.json. Dogfood: .ai/docs-map.yaml deste repo lista 9 docs vivos.
- Skill /finish reescrita: ensina rodar docs-check antes, registrar com --docs-touched/--docs-skip; agent_skill e claude_skill regenerados via render-skills.py.
- Docs novos: how-to/manter-docs-atualizados.md, reference/docs-map.md, explanation/por-que-docs-hook.md, adr/0005-docs-hook-no-finish.md. ADR README, files.md, cli.md, visao-geral.md, CHANGELOG, CLAUDE.md, AGENTS.md, CONTRIBUTING.md, README.md atualizados pra refletir o novo passo.
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/ai.py doctor -> AI process files OK.
- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- python scripts/ai.py docs-check F-010 -> lista 9 candidatos corretos (FEATURES, CHANGELOG, README, cli.md, visao-geral, adr/, CLAUDE.md, AGENTS.md, CONTRIBUTING.md) com motivos task-finished/touched/architectural-decision.
- python scripts/ai.py finish F-010 --no-commit (sem flags de docs) -> bloqueia com exit 1 e imprime o painel completo. Hook funciona.

### Validacao pendente

- Nenhuma.

## [F-009] Migrar layout para plugin oficial Claude Code (A+B base) + ADR-0005

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
- **Tipo:** Feature
- **Contexto:** Pesquisa arquitetural (2026-05-31) confirmou opcao A+B com alvo tri-agente (Claude principal, Codex secundario, Antigravity terciario). Esta demanda e o fundamento estrutural: (1) adicionar .claude-plugin/plugin.json na raiz com manifest oficial; (2) reorganizar a saida do render-skills.py para o layout root-level oficial (skills/, commands/, hooks/, bin/) em vez de skills/generated/.claude/...; (3) manter skills/generated/.agents/ para Codex+Antigravity via AGENTS.md+SKILL.md cross-tool; (4) preservar scripts/ai.py como motor (skills continuam thin wrappers); (5) escrever ADR-0005 documentando a decisao com links pra https://code.claude.com/docs/en/plugins e o padrao AGENTS.md (Linux Foundation). Bloqueia o restante do backlog (marketplace.json, MCP server, PreToolUse hook, compat cross-agent, consolidacao AGENTS/CLAUDE, docs Diataxis).

### Arquivos modificados/criados

- `FEATURES.md`
- `.claude-plugin/plugin.json`
- `plugin-src/manifest.yaml`
- `scripts/render-skills.py`
- `scripts/ai.py`
- `skills/ai-process/SKILL.md`
- `skills/feature/SKILL.md`
- `skills/issue/SKILL.md`
- `skills/backlog/SKILL.md`
- `skills/promote/SKILL.md`
- `skills/ready/SKILL.md`
- `skills/finish/SKILL.md`
- `skills/status/SKILL.md`
- `.agents/skills/ai-process/SKILL.md`
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
- `.ai/docs-map.yaml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/render-check.yml`
- `.claude-plugin/marketplace.json`
- `.claude/settings.json`
- `.ai/backlog.json`
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Layout oficial de plugin Claude Code: .claude-plugin/plugin.json (name=ai) na raiz expoe os 8 verbos sob namespace ai (/ai:feature, /ai:issue, etc.). Source do manifest movido de skills/manifest.yaml para plugin-src/manifest.yaml. render-skills.py reduzido de 4 destinos para 2: skills/<verbo>/SKILL.md (output do plugin Claude oficial) + .agents/skills/<verbo>/SKILL.md (cross-tool Codex+Antigravity via convencao AGENTS.md). Removidos skills/generated/ e .claude/skills/ na raiz. ADR-0006 criado documentando a decisao com tradeoffs e alternativas rejeitadas (standalone, nome longo, source em path nao-padrao, bin/ ja nesta demanda). Docs vivos atualizados: CLAUDE.md, AGENTS.md, cli.md, files.md, visao-geral.md, CHANGELOG.md, README.md, CONTRIBUTING.md, instalar-em-outro-projeto.md, SECURITY.md, PULL_REQUEST_TEMPLATE.md, render-check.yml, docs-map.yaml. scripts/ai.py: help text do subcomando render ajustado.
- Scope expandido durante validacao: alem do plugin oficial Claude Code (item 1-6 do ADR-0006), incluido marketplace local autoregistrado (item 7). Adicionados .claude-plugin/marketplace.json (catalogo name=ai-process-pack, plugin source=./) e .claude/settings.json (extraKnownMarketplaces com source directory + enabledPlugins habilitando ai@ai-process-pack). Resultado: ao abrir o repo em Claude Code (primeira vez), o user recebe prompt de trust + install e os atalhos /ai:feature, /ai:issue, etc ficam disponiveis nas sessoes futuras sem precisar de --plugin-dir manual. Absorve a demanda B-001 do backlog. ADR-0006 atualizado com item 7 da Decisao, consequencia positiva da descoberta automatica recuperada, e nota de versao minima (Claude Code 2.1.x+) nas Consequencias. CLAUDE.md, README.md, instalar-em-outro-projeto.md atualizados com as 3 vias de instalacao (dogfood/marketplace publico/copia manual). CHANGELOG.md ganhou nova entry Added sobre o marketplace local.
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- python scripts/ai.py doctor -> AI process files OK.
- python -m unittest tests.test_smoke -v -> OK, 1 teste passou. Smoke nao depende dos paths novos, mas confirma que scripts/ai.py continua intacto.
- Get-ChildItem skills, .agents/skills -Directory confirma 8 pastas em cada (ai-process, backlog, feature, finish, issue, promote, ready, status). 16 SKILL.md no total.
- python -m unittest tests.test_smoke -v -> OK, 1 teste passou.
- Get-ChildItem .claude-plugin confirma 2 arquivos (marketplace.json, plugin.json). Get-ChildItem .claude confirma settings.json. Get-ChildItem skills, .agents/skills -Directory confirma 8 pastas em cada (16 SKILL.md no total).

### Validacao pendente

- Nenhuma.

## [F-008] Criar ADRs iniciais (4 decisoes fundadoras)

- **Status:** Validada
- **Origem:** AI process (2026-05-31)
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
- `.ai/current-task.json`
- `.ai/tasks.json`

### O que foi feito

- Demanda criada via ai-process.
- Criada estrutura docs/adr/ com README (indice+convencoes), template, e 4 ADRs iniciais (script fonte de verdade, lock por commit-message, JSON/Markdown dual, chat-title sincronizado). Links cruzados: docs/README.md e README.md raiz apontam para adr/; explanation/por-que-script-fonte-da-verdade.md e explanation/por-que-lock.md ganharam banner apontando o ADR como decisao canonica (explanation continua como versao pedagogica). Convencao: NNNN-kebab.md, status Proposta/Aceita/Substituida/Depreciada, secoes Contexto/Decisao/Consequencias/Alternativas/Links.
- Demanda finalizada via ai-process.

### Validacao feita

- python scripts/ai.py doctor -> AI process files OK.
- python scripts/render-skills.py --check -> OK: 16 alvo(s) em sincronia com o manifest.
- ls docs/adr/ confirma 6 arquivos: README.md, template.md, 0001..0004.

### Validacao pendente

- Nenhuma.

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

- **Status:** Validada
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
- Demanda finalizada via ai-process.

### Validacao feita

- python -m unittest tests.test_smoke -v -> OK, 1 teste passou em 1.365s.

### Validacao pendente

- Nenhuma.

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

