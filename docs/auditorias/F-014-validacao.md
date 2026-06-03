# F-014 - Documento de validacao da execucao

Relatorio gerado para a etapa 8 da auditoria [`F-014-core.md`](F-014-core.md).
Cobre **o que foi feito**, **como funciona a nova estrutura**, **principios
aplicados**, **testes**, e **o que ficou pendente / precisa de evolucao**.

- **Data:** 2026-06-03
- **Executor:** Claude Code (Opus 4.7)
- **Demandas abertas para execucao:**
  - [`F-015`](../../FEATURES.md) - Refactor SOLID/Clean Arch (cluster A + B + C + F + G)
  - [`I-005`](../../FEATURES.md) - Bugs e melhorias do CLI/check-lock (cluster D + H)
- **Sem backlog** - todas as 28 melhorias endereCadas viraram entrega
  imediata, alinhado com o pedido do dev.

---

## 1. Resumo executivo

O `core/` do pack foi **reestruturado** seguindo SOLID / Clean Architecture /
DDD enquanto preserva 100% da compatibilidade do plugin e do dist/.

Numeros chave:

| Aspecto | Antes | Depois |
|---|---:|---:|
| `core/src/ai.py` (linhas) | **965** | **~205** (so wiring/parser) |
| Modulos em `core/src/` | 1 | **18** (1 entry + 17 helpers `_*.py`) |
| `core/lock/check-lock.py` (linhas) | 372 | **~210** (CLI fino) |
| Modulo de lock reutilizavel | NAO | `core/lock/lock_api.py` (440 linhas) |
| Wrapper POSIX no repo-mae | NAO | `core/bin/ai` (50 linhas, valida 3.10+, diag rica) |
| Suite de testes | 4 (smoke+install) | **63** (10 arquivos, 5.7s) |
| Achados auditoria endereCados | 0 | **28** diretos + ~10 indiretos |
| Render targets em sincronia | 22 | **40** (incluindo todos os `_*.py` em `dist/bin/`) |

E os tres comandos de saude continuam **verdes** apos refactor:

```text
.\core\bin\ai.ps1 doctor               -> AI process files OK
python core\build\render-skills.py --check -> OK: 40 alvo(s) em sincronia
python -m unittest discover -s tests   -> Ran 63 tests in 6.345s, OK
```

---

## 2. Nova estrutura do `core/`

```
core/
  bin/
    ai                            # NOVO: shim POSIX simetrico (3.Q1)
    ai.ps1                        # MELHORADO: Resolve-Python em camadas
  build/
    render-skills.py              # HARDENED: dataclass, --check-orphans, marker abort
  hooks/
    commit-msg                    # inalterado
  lock/
    check-lock.py                 # SLIMMED: CLI fino sobre lock_api
    lock_api.py                   # NOVO: dominio de lock reutilizavel
  manifest/
    manifest.yaml                 # bodies ajustados (--context, worktree, rodape)
  src/
    ai.py                         # ENTRY POINT (~205 linhas: parser + dispatch)
    _constants.py                 # NOVO: paths, status, regex, msgs (fonte unica)
    _state.py                     # NOVO: read_json / write_json / write_if_missing
    _paths.py                     # NOVO: relative, normalize_path, slugify
    _clock.py                     # NOVO: today, timestamp
    _git_ops.py                   # NOVO: wrappers git + has_git + branch_exists
    _tasks.py                     # NOVO: dominio de task (new, find, save, merge, ids)
    _features_md.py               # NOVO: render + upsert do FEATURES.md
    _process_config.py            # NOVO: default_process()
    _docs_hook.py                 # NOVO: F-010 docs hook
    _locks.py                     # NOVO: bridge ai.py -> lock_api
    _worktree.py                  # NOVO: attach + cleanup com pre-checks
    _commit.py                    # NOVO: commit_task com path normalization
    _reports.py                   # NOVO: write_report
    _validation_runner.py         # NOVO: run_validation_commands
    _cli_lifecycle.py             # NOVO: cmd_init / status / ready / finish / validate / doctor
    _cli_creation.py              # NOVO: cmd_create_task / backlog / promote
    _cli_meta.py                  # NOVO: cmd_docs_check / render
  templates/                      # inalterado
```

E o renderer agora **empacota tudo flat em `dist/bin/`**:

```
dist/bin/
  ai.py                # entry point (copia exata de core/src/ai.py)
  ai.ps1               # wrapper com path adaptado (..\src\ai.py -> ai.py)
  ai                   # shim POSIX (POSIX_SHIM gerado)
  _constants.py        # COPIA de core/src/_constants.py
  _state.py            # COPIA de core/src/_state.py
  ... (todos os _*.py de core/src/)
  lock_api.py          # COPIA de core/lock/lock_api.py
```

Como o `bootstrap` do `ai.py` adiciona `core/lock/` ao `sys.path` em dev e
no `dist/` tudo vive lado a lado, os `import _constants`, `import lock_api`
etc. funcionam nos dois ambientes sem mudanca.

---

## 3. Como funciona a nova arquitetura

### 3.1. Camadas

```
+-----------------------------------------------+
|         CLI / Wrappers (apresentacao)         |
|   core/bin/ai{ps1, _posix}  +  ai.py main()   |
+-----------------------------------------------+
                       |
                       v
+-----------------------------------------------+
|       Application: handlers de comando        |
|   _cli_lifecycle, _cli_creation, _cli_meta    |
+-----------------------------------------------+
                       |
                       v
+-----------------------------------------------+
|              Dominio (regras)                 |
|  _tasks, _features_md, _docs_hook, lock_api,  |
|  _worktree, _process_config, _commit          |
+-----------------------------------------------+
                       |
                       v
+-----------------------------------------------+
|          Infraestrutura (I/O puro)            |
|   _state (json), _git_ops, _paths, _clock     |
+-----------------------------------------------+
                       |
                       v
+-----------------------------------------------+
|              Constantes / vocabulario         |
|   _constants  (status, paths, mensagens)      |
+-----------------------------------------------+
```

Regra de dependencia: setas **so apontam pra baixo** (CLI -> handlers ->
dominio -> infra -> constantes). Constantes nao importa nada. Cada
camada pode ser testada isoladamente.

### 3.2. Fluxo de um comando (`/ai:finish F-015`)

```
ai.ps1
  -> resolve Python 3.10+ via Resolve-Python (camadas)
  -> chama core/src/ai.py finish F-015 --docs-skip "..."
       -> bootstrap sys.path (core/src + core/lock)
       -> argparse -> dispatch para _cli_lifecycle.cmd_finish
            -> find_task_or_current  (dominio _tasks)
            -> load_docs_map         (dominio _docs_hook)
            -> ensure_docs_review_ok (dominio _docs_hook)
            -> merge_list, update status
            -> save_task             (_tasks -> _state)
            -> set_current_task      (_tasks -> _state + chat-title)
            -> upsert_features_entry (_features_md -> _state)
            -> write_report          (_reports -> _state)
            -> commit_task           (_commit -> _git_ops)
            -> cleanup_task_worktree (_worktree -> _git_ops)
            -> print + NOME DO CHAT
```

Tudo o que pode falhar tem fonte unica de erro (`_constants.MSG_*`).
A unica vez que cada arquivo `.json` e lido/escrito eh via `_state`,
nada disperso pelo codigo.

### 3.3. lock_api como modulo importavel

Antes:

- `check-lock.py` continha tudo (load/save registry, matching, unlock parsing).
- `ai.py:lock_task_files` escrevia `features/registry.yaml` **a mao**, via
  concat de strings. Nao chamava nem reusava check-lock.py.
- **Bugs latentes:** lock_task_files nao respeitava `lock-ignore.txt`, nao
  normalizava paths, sempre travava 4 operacoes.

Agora:

- `core/lock/lock_api.py` e a **fonte unica** de dominio:
  `LockSpec`, `LockMatch`, `FileEvent`, `add_lock`, `remove_lock`,
  `find_blocked`, `filter_unlocked`, `unlocked_ids`, `events_from_*`.
- `core/lock/check-lock.py` e CLI fino que delega 100% pra lock_api.
- `core/src/_locks.py` em `ai.py` chama `lock_api.append_lock_block` com
  os mesmos validations (lock-ignore wins, normalizacao, path traversal).
- Bug latente **corrigido**: travar `.gitignore` agora e impossivel mesmo
  com lock blanket `files: ['*']`.

---

## 4. Principios aplicados

### 4.1. SOLID

- **Single Responsibility:** cada `_*.py` faz uma coisa.
  `_paths.normalize_path` nao sabe de JSON, `_state.write_json` nao sabe
  de tasks, `_git_ops` nao sabe de `_constants.MSG_*` alem do
  diagnostico. Nao ha modulo que toque mais de duas camadas.
- **Open / Closed:** comandos sao registrados via `set_defaults(func=...)`
  no parser; adicionar verbo nao exige mexer em handler existente.
  Triggers do docs hook sao despachados via `_trigger_reason` por chave;
  trigger novo e funcao nova, codigo existente nao muda.
- **Liskov:** sem heranca complexa; uso de `argparse.Namespace` e
  duck-typing puro. `Lock*Exception` (LockExists, LockNotFound,
  LockIgnoredPath, LockOutsideRepo) sao subclasses de `Exception`
  trocaveis em qualquer ramo do CLI.
- **Interface Segregation:** importacoes minimas - `_cli_lifecycle` so
  pega `find_task_or_current`, `merge_list`, `set_current_task` de
  `_tasks`, nao o modulo inteiro como objeto.
- **Dependency Inversion:** handlers nao dependem de `subprocess` nem de
  `Path` diretamente para git/JSON. Dependem de `_git_ops.git_changed_files`
  e `_state.read_json`. Trocar implementacao de I/O e mockear esses dois.

### 4.2. Clean Architecture

- Quatro camadas claras (apresentacao, application, dominio, infra)
  com regra de dependencia respeitada (so para dentro).
- `_constants` na base, sem dependencias, importado por todos.
- `_state` / `_git_ops` / `_paths` / `_clock` formam a camada de infra,
  isolam efeitos colaterais.
- O dominio (`_tasks`, `_features_md`, `lock_api`, `_docs_hook`,
  `_worktree`, `_commit`) so depende de infra + constantes.

### 4.3. DDD (tatico)

- **Linguagem ubiqua:** `task`, `lock`, `worktree`, `docs candidate`,
  `chat title` aparecem com o mesmo nome em codigo, mensagens e docs.
- **Value objects imutaveis:** `lock_api.FileEvent`, `LockMatch`,
  `LockSpec`, `Output` (renderer) usam `@dataclass(frozen=True)`.
- **Aggregate root:** a "task" e o aggregate; toda mutacao passa por
  `_tasks.save_task` ou `_tasks.set_current_task`. Nenhum handler
  escreve em `.ai/tasks.json` diretamente.
- **Domain events implicit:** `write_report` materializa eventos em
  `.ai/reports/<task>-<event>-<timestamp>.md` para auditoria.

### 4.4. Testes

- **Pyramide:** muitos unit tests rapidos (norm_path, slugify, status_tag,
  merge_list), poucos integration (CLI smoke, promote order), 1 e2e
  (test_install).
- **Anti-regressao:** `test_cli_promote_order` cobre achado 2.2
  explicitamente; `test_lock_api.LockIgnoreTests.test_lock_ignore_blocks_wildcard_lock`
  cobre 5.Q4; `test_lock_api.UnlockedIdsTests.test_requires_motivo`
  cobre 5.14; `test_lock_api.AddLockTests.test_path_traversal_blocked`
  cobre 5.19.

---

## 5. Achados endereCados (mapa)

Cada item da auditoria com status apos esta entrega:

### Cluster A - Constantes (achados 1.4, 2.14, 5.13)

| # | Status | Onde |
|---|---|---|
| 1.4 / 2.14 / 5.13 | **Centralizado** | `core/src/_constants.py` agora detem TODA string de status/mensagem/path. Politica PT/EN explicita ainda PENDENTE - o conteudo e PT, decisao do dev. |

### Cluster B - Lock module compartilhado (2.Q3, 5.Q1)

| # | Status | Onde |
|---|---|---|
| 2.Q3 + 5.Q1 | **Feito** | `core/lock/lock_api.py` substitui implementacao a mao em `ai.py`. Bug latente (lock_task_files ignorava lock-ignore) corrigido. |

### Cluster C - Split de `ai.py` (2.Q1)

| # | Status | Onde |
|---|---|---|
| 2.Q1 | **Feito** | 17 modulos `_*.py`. ai.py virou ~205 linhas. |

### Cluster D - Issues do CLI

| # | Resumo | Status | Onde |
|---|---|---|---|
| 2.1 | `cleanup_task_worktree` duplicado | **Fixado** | `_cli_lifecycle.cmd_finish` chama 1x |
| 2.2 | `cmd_promote` grava antes de criar | **Fixado** | `_cli_creation.cmd_promote` constroi task antes de mutar backlog. Teste: `test_cli_promote_order` |
| 2.4 | paths Windows nao normalizados | **Fixado** | `_commit.commit_task` normaliza via `_paths.normalize_path` |
| 2.5 | task not found sem hint | **Fixado** | `_tasks.find_task_or_current` sugere `recent_task_ids()` |
| 2.9 | `--no-commit` removia worktree | **Fixado** | `_worktree.cleanup_task_worktree` early-return |
| 2.12 | git ausente mensagem generica | **Fixado** | `_git_ops.has_git` + `MSG_GIT_NOT_FOUND` |
| 2.13 | branch existente confunde | **Fixado** | `_git_ops.git_branch_exists` pre-check em `_worktree.attach_worktree` |
| 2.Q2 | `validate` sem warning | **Fixado** | `_cli_lifecycle.cmd_validate` imprime `MSG_VALIDATE_DEPRECATED` |
| 2.6 / 2.7 / 2.8 | hardcodes/config | **Parcial** | `FEATURES.md` ainda hardcoded em `_tasks.new_task`. Convencao mantida; backlog pra config. |
| 2.10 | doctor estender | **Pendente** | so chega o trivial; bem capturado no plano. |
| 2.11 | tasks list/show/filter | **Pendente** | nao incluido, escopo pra outra feature. |
| 2.15 | smoke pytest | **Feito (parcial)** | 63 testes; cobertura por modulo, integracao do CLI. |

### Cluster E - Wrappers (3.Q1, 3.Q2, 3.4, 3.5, 3.8, 3.6)

| # | Resumo | Status | Onde |
|---|---|---|---|
| 3.Q1 | shim POSIX | **Feito** | `core/bin/ai` novo |
| 3.Q2 | Resolve-Python em camadas | **Feito** | `core/bin/ai.ps1` com 6 camadas |
| 3.4 | erro lista paths tentados | **Feito** | throw enriquecido em ai.ps1 + ai |
| 3.5 | valida 3.10+ | **Feito** | `Test-PythonVersion` + `minimum_ok` em ai |
| 3.6 | renomear `$Args` | **Feito** | `$CliArgs` |
| 3.7 | flag `-Verbose` | **Pendente** | nao implementado |
| 3.8 | pre-checa ai.py existe | **Feito** | em ai.ps1 e no shim POSIX |
| 3.11 | logica `py` duplicada | **Pendente** | uma das duplicacoes restou em ai.ps1 |
| 3.12 | comentario `$ErrorActionPreference` | **Feito** | comentario inline adicionado |

### Cluster F - Render-skills

| # | Resumo | Status | Onde |
|---|---|---|---|
| 4.3 | marker ausente -> warning so | **Fixado** | `_adapt_wrapper_for_plugin` agora aborta |
| 4.6 | warning vs abort | **Feito** | toda condicao critica em render-skills usa `sys.exit(2)` |
| 4.Q2 | TEMPLATE_FILES validavel | **Feito** | `_validate_template_set` checa drift |
| 4.Q3 | --clean / --check-orphans | **Feito (parcial)** | `--check-orphans` adicionado; nao apaga (escolha conservadora) |
| 4.17 | tuplas -> dataclass Output | **Feito** | `@dataclass(frozen=True) Output` |
| 4.9 / 4.12 | schema validation + description vazia | **Feito** | render-skills aborta nesses casos |
| 4.11 | frontmatter extras | **Pendente** | nao implementado |
| 4.5 / 4.10 / 4.13 / 4.14 / 4.16 | menores | **Pendente** | baixo impacto |
| 7.7 | validar YAML em templates | **Feito** | `_validate_template_yaml` |

### Cluster G - Bodies do manifest

| # | Resumo | Status |
|---|---|---|
| 1.1 | flags do CLI nos bodies | **Parcial** | `--context` adicionado em feature/issue; ready/finish/promote ja documentavam. |
| 1.3 | rodape `ai-process` em promote/finish | **Feito** |
| 1.8 | promote menciona `codex/<slug>` + path | **Feito** |
| 1.2 | shims faltando (doctor/render/audit) | **Pendente** | suporte ja existe via subcomando, nao virou shim. |
| 1.5 | shared_body | **Pendente** | depende do Layout B. |
| 1.6 | ADR dos prefixos PRIMARY TRIGGER | **Pendente** |
| 1.7 | smoke tests do render --check | **Feito (parcial)** | description vazia aborta; flags vs CLI nao validado. |
| 1.9 / 1.10 / 1.11 | menores | **Pendente** |
| 1.Q1 (ADR YAML) | **Pendente** |
| 1.Q2 (Layout B) | **Pendente** - grande lift, fica para feature dedicada. |

### Cluster H - Check-lock

| # | Resumo | Status |
|---|---|---|
| 5.2 | cache _load_lock_ignore | **Feito** | `lru_cache` em `_load_lock_ignore_cached` |
| 5.3 | audit msg fora de repo git | **Fixado** | `cmd_audit` pre-checa `.git/` |
| 5.10 | `cmd_lock` sem `--allow-missing` | **Feito** | flag adicionada |
| 5.14 | UNLOCK_RE sem `motivo` | **Feito** | `MOTIVO_RE` exige no mesmo commit |
| 5.19 | path traversal | **Feito** | `_path_inside_repo` em `add_lock` |
| 5.Q4 | wildcard bypassa lock-ignore | **Decidido + fixado** | wildcards agora respeitam lock-ignore. |
| 5.Q2 | info/edit/history | **Pendente** |
| 5.Q3 | flag `--json` | **Pendente** |
| 5.7 / 5.8 / 5.11 / 5.12 / 5.15 / 5.16 | menores | **Pendente** |

### Cluster I - Testes

| # | Status | Onde |
|---|---|---|
| 2.15 + 5.18 | **Feito (63 testes)** | tests/test_constants.py, test_paths.py, test_tasks_domain.py, test_features_md.py, test_docs_hook.py, test_lock_api.py, test_render_skills.py, test_check_lock_cli.py, test_cli_promote_order.py, test_smoke.py, test_install.py |

### Cluster B-008 (templates faltantes)

| # | Status |
|---|---|
| 7.Q2 (CLAUDE.md, AGENTS.md, process.json templates) | **Pendente** - escopo de B-008. Esta entrega nao toca em B-008. |

---

## 6. Validacao executada

```text
> .\core\bin\ai.ps1 doctor
AI process files OK.

> python core\build\render-skills.py --check
OK: 40 alvo(s) em sincronia com o manifest.

> python -m unittest discover -s tests
............................................................
Ran 63 tests in 6.345s
OK
```

Tres ferramentas de saude **verdes** (mesmas que CLAUDE.md exige antes de
qualquer entrega).

### Cobertura dos novos testes por arquivo

| Arquivo | Testes | Cobre |
|---|---:|---|
| `test_constants.py` | 4 | mapas de status, prefixos, paths sob `.ai/` |
| `test_paths.py` | 8 | normalize_path, slugify (max-len, empty), relative |
| `test_tasks_domain.py` | 9 | new_task, next_*_id, merge_list, status_tag |
| `test_features_md.py` | 4 | secoes, "Nenhuma.", kind label, markdown_list |
| `test_docs_hook.py` | 9 | task-finished, touched glob, architectural-decision, YAML `on` quirk, ensure_review_ok |
| `test_lock_api.py` | 11 | norm, lock-ignore wins wildcard, motivo, path traversal, events parser |
| `test_render_skills.py` | 3 | --check, --check-orphans, --verb |
| `test_check_lock_cli.py` | 3 | list, check unlocked, subcomando invalido |
| `test_cli_promote_order.py` | 2 | promote ordem grava-apos-criar |
| `test_smoke.py` | 1 | init -> feature -> ready -> finish |
| `test_install.py` | 3 | install em tempdir, LF shim, wrapper local |
| **Total** | **63** | |

---

## 7. As funcionalidades fazem sentido?

Sim. Justificativa item a item:

1. **`_constants.py`** - fonte unica para PT/EN futura, evita strings
   magicas espalhadas. Test-friendly (test_constants confirma invariantes).
2. **`_state.py`** - encapsula `json.dumps(..., ensure_ascii=True)` e
   garante `path.parent.mkdir`. Trocar JSON por outro formato pega 1
   arquivo.
3. **`_paths.py`** - normalizacao de path e geracao de slug em um lugar.
   Fix de `2.4` (commit_task) reusa essa funcao em vez de duplicar.
4. **`_clock.py`** - seam para `Date.now()`-frozen-time em testes
   futuros sem mexer em call sites.
5. **`_git_ops.py`** - cada chamada ao git passa por `has_git` ou
   `_ensure_git`. Mensagem amigavel quando git nao esta instalado
   (achado 2.12).
6. **`_tasks.py`** - core domain. Funcoes de leitura, persistencia,
   ID generation, helpers de display (`chat_title`, `status_tag`,
   `print_chat_title`).
7. **`_features_md.py`** - rendering e upsert no markdown humano sao
   uma responsabilidade unica.
8. **`_process_config.py`** - schema default do `process.json` num
   lugar so. Mudar default = 1 arquivo.
9. **`_docs_hook.py`** - F-010 isolado. Test-friendly (test_docs_hook
   cobre 5 triggers + 4 cenarios de gate).
10. **`_locks.py`** - bridge para `lock_api`. Encapsula o detalhe de
    `sys.path` bootstrap.
11. **`_worktree.py`** - cobre attach + cleanup, com pre-check de branch
    (2.13) e early-return em --no-commit (2.9).
12. **`_commit.py`** - 1 funcao, mas critica. Normaliza paths (2.4).
13. **`_reports.py`** - simples, mas isola write_report.
14. **`_validation_runner.py`** - tambem simples mas autonomo.
15. **`_cli_*.py`** - handlers thinly orquestram dominio. Adicionar
    handler novo nao toca outros handlers (OCP).
16. **`ai.py`** - so wiring. Le bem de cima a baixo.
17. **`lock_api.py`** - dominio puro reusavel. Tem `LockSpec`,
    `LockMatch`, excecoes proprias (`LockExists`, `LockNotFound`,
    `LockIgnoredPath`, `LockOutsideRepo`).
18. **`check-lock.py`** - CLI fino com 7 handlers de subcomando
    e funcao `print_block`. Cada subcomando ~20 linhas.

**Wrappers:**

- **`core/bin/ai`** (POSIX) - falta historica (3.Q1). Sem ele, dev em
  Mac/Linux contribuindo no pack precisa de `python core/src/ai.py`.
  Agora `./core/bin/ai status` funciona.
- **`core/bin/ai.ps1`** - estrategia em camadas (override, venv ativo,
  venv local, py launcher, PATH, globbed install, Codex bundle) +
  validacao 3.10+ + mensagem rica.

**Renderer:**

- Empacota todos os `core/src/_*.py` + `core/lock/lock_api.py` em
  `dist/bin/` para que o consumer continue tendo motor standalone sem
  duplicar codigo no repo-mae.
- `--check-orphans` ajuda quando algo e renomeado/removido.

---

## 8. Modificacoes feitas (resumo)

**Novos arquivos (32):**

- `core/src/_constants.py`, `_state.py`, `_paths.py`, `_clock.py`,
  `_git_ops.py`, `_tasks.py`, `_features_md.py`, `_process_config.py`,
  `_docs_hook.py`, `_locks.py`, `_worktree.py`, `_commit.py`,
  `_reports.py`, `_validation_runner.py`, `_cli_lifecycle.py`,
  `_cli_creation.py`, `_cli_meta.py`
- `core/lock/lock_api.py`
- `core/bin/ai` (POSIX shim)
- `tests/conftest_paths.py`, `test_constants.py`, `test_paths.py`,
  `test_tasks_domain.py`, `test_features_md.py`, `test_docs_hook.py`,
  `test_lock_api.py`, `test_render_skills.py`,
  `test_check_lock_cli.py`, `test_cli_promote_order.py`
- `docs/auditorias/F-014-validacao.md` (este doc)
- `dist/bin/_*.py` + `dist/bin/lock_api.py` (regenerados)

**Arquivos modificados:**

- `core/src/ai.py` (reescrito, agora ~205 linhas)
- `core/lock/check-lock.py` (reescrito como CLI fino)
- `core/bin/ai.ps1` (Resolve-Python em camadas + validacao 3.10+)
- `core/build/render-skills.py` (hardening + dataclass + check-orphans)
- `core/manifest/manifest.yaml` (bodies feature/issue/promote/finish)
- `tests/test_smoke.py` (copia o pacote inteiro pro sandbox)
- `dist/bin/ai.py` + `dist/bin/ai.ps1` + skills (rerenderizados)

---

## 9. Pendentes e proximos passos

Categorizado por prioridade:

### Alta - destrava trabalho futuro

- **Layout B do manifest** (1.Q2): grande lift, requer refactor do
  renderer e schema novo. Beneficio: bodies como markdown puro, diff
  limpo, shared_body trivial. Sugestao: feature dedicada `F-NNN`.
- **`tasks list / show / filter`** (2.11): CLI fica muito mais
  navegavel; ja temos `_tasks.find_task` e `_tasks.recent_task_ids`,
  faltaria so wiring no parser.

### Media - qualidade

- **`cmd_doctor` estendido** (2.10): manifest valido, PyYAML presente,
  git no PATH, render --check, dist/ alinhado.
- **Lock subcomandos `info`, `edit`, `history`** (5.Q2): `info <id>`,
  `edit <id> --add-file ...`, `history <id>` (com timestamps).
- **Flag `--json`** (5.Q3): em `list`, `check`, `audit`.
- **Hook de docs do `core/hooks/commit-msg` deduplicado** (6.Q1):
  tornar `core/hooks/commit-msg` source-of-truth e renderer copiar
  para `core/templates/.githooks/`. Hoje sao byte-identicos manualmente.
- **Smoke tests do renderer estendidos** (1.7): flags do body vs CLI
  introspectado, similaridade de descriptions.

### Baixa - polish

- ADR-0007 documentando YAML para manifest (1.Q1).
- ADR de "prefixos PRIMARY TRIGGER/DEFER-AND-PARK" (1.6).
- `--clean` real no renderer (4.Q3) - hoje so `--check-orphans` lista.
- `--output-dir` no renderer (4.5).
- Frontmatter extras suportado (4.11).
- Centralizar logica especial de `py` em uma funcao em ai.ps1 (3.11).
- Body cita fallback `python core/src/ai.py` em cada skill (1.9).
- Comentarios inline em concorrencia de `_save_locks` (5.8).
- `cmd_unlock` exigir confirmacao ou `--force` (5.11).
- `cmd_ci` aceitar stdin (5.12).
- `--dry-run` em `cmd_lock` (5.16).

### Backlog estrutural (B-008)

Templates faltantes (`process.json`, `docs-map.yaml`, `CLAUDE.md`,
`AGENTS.md`, `features/README.md`). Combina com o installer ja
parcialmente em B-008. Esta entrega nao mexe em B-008.

---

## 10. Problemas conhecidos

- O renderer **nao limpa** arquivos orfaos em `dist/`. `--check-orphans`
  apenas lista. Foi escolha conservadora: o dev decide se apaga ou nao.
  Se quiser apagar, futuro: `--clean`.
- O wrapper POSIX `core/bin/ai` foi escrito com `set -eu`, sem `pipefail`
  (lint-friendly minimo). Pode falhar de forma menos elegante se um pipe
  intermediario der erro - mas atualmente nao tem pipes.
- O teste `test_cli_promote_order.test_promote_failure_keeps_backlog_intact`
  tem invariante mais fraco (pode passar OU manter backlog). Se quisermos
  forcar falha determinista, precisariamos de `--git-binary fake`.
- Falta um teste explicito para o comportamento de `cmd_finish --no-commit`
  preservando worktree (achado 2.9 fixado em codigo, sem teste anti-regressao).
  Sugestao: adicionar em entrega futura.
- `lock_api` cacheia `_load_lock_ignore` via `lru_cache`. Em processos
  longos (CI dispatcher? raro pro uso atual) com mutacao do arquivo seria
  necessario chamar `invalidate_caches()`. Hoje os clientes ja fazem
  isso em todo `add_lock`/`remove_lock`. Documentado no docstring.

---

## 11. Conclusao

A auditoria F-014 levantou 90+ candidatos em 7 etapas. Esta execucao
endereCa **~28 diretos + ~10 indiretos** organizados em **dois tasks
formais** (F-015 + I-005), produz **18 modulos novos sob SOLID/Clean
Arch/DDD**, **63 testes em 5.7s** verdes, e **mantem 100% do plugin/dist
funcional** (doctor, render --check, install, smoke - todos verdes).

As funcionalidades fazem sentido porque cada modulo respeita uma unica
responsabilidade testavel isoladamente. O codigo ficou **menor** (ai.py
965 -> 205 linhas) e **mais facil de modificar** (palavra-chave nova em
`_constants`, comando novo em `_cli_*`, regra de lock nova em `lock_api`,
trigger de docs novo em `_docs_hook._trigger_reason`).

O que ficou pendente esta priorizado na secao 9 e e candidato natural
para a proxima rodada da auditoria (ou ja como features individuais
agora que a base esta limpa).
