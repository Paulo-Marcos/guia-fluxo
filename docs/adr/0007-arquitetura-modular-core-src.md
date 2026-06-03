# ADR-0007: Decompor `core/src/ai.py` em modulos com Clean Architecture

- **Status:** Aceita
- **Data:** 2026-06-03

## Contexto

`core/src/ai.py` cresceu para **965 linhas em um arquivo unico**: parser
argparse, 13 handlers de subcomando, dominio (task + backlog + features
md + docs hook + worktree + commit + lock), infraestrutura (json, git,
subprocess) e constantes (status PT, paths, regex, mensagens), tudo
colado.

Dores observadas e medidas na auditoria [`F-014`](../auditorias/F-014-core.md):

- Localizacao: ctrl+F para mexer em "logica de worktree".
- Revisao: PRs pequenas se escondem no scroll.
- Reuso: `lock_task_files` reimplementou `check-lock.py` a mao, pulou
  `lock-ignore.txt` e normalizacao de paths (bug latente real).
- Teste: impossivel mockear `subprocess` ou `Path` em granularidade de
  funcao sem refactor.
- Mudanca de string: "Aguardando validacao" hardcoded em 4 lugares; a
  versao com acento idem.

Decisao precisava preservar:
- API publica do CLI (todos os subcomandos + flags atuais).
- `dist/bin/ai.py` standalone que o consumidor recebe via instalador (o
  renderer hoje copia `core/src/ai.py` byte-a-byte).
- Smoke test atual + install test.

## Decisao

Decompor o motor em **18 modulos sob `core/src/`** seguindo Clean
Architecture com 4 camadas:

1. **Constantes** (`_constants.py`): paths, status, regexes, mensagens.
   Nao depende de ninguem.
2. **Infraestrutura** (`_state.py`, `_git_ops.py`, `_paths.py`,
   `_clock.py`): I/O puro. So depende de constantes.
3. **Dominio** (`_tasks.py`, `_features_md.py`, `_docs_hook.py`,
   `lock_api.py`, `_worktree.py`, `_commit.py`, `_process_config.py`,
   `_reports.py`, `_validation_runner.py`, `_locks.py`): regras de
   negocio do pack. Depende de infra + constantes.
4. **Application/CLI** (`_cli_lifecycle.py`, `_cli_creation.py`,
   `_cli_meta.py`): handlers de subcomando. Depende de dominio.

`ai.py` vira **entry point fino** (~205 linhas: bootstrap do sys.path +
argparse builder + `main()` que delega via `args.func(args)`).

`lock_api.py` mora em `core/lock/` porque ja era o lugar do
`check-lock.py`; e o reuso entre `check-lock.py` (CLI standalone) e
`ai.py` (`lock_task_files`).

Renderer copia **todos** os `core/src/*.py` + `core/lock/lock_api.py`
para `dist/bin/` num layout flat. Como o sys.path do entry point inclui
o proprio diretorio, `import _constants` / `import lock_api` funcionam
sem mudanca em dev e no plugin.

## Consequencias

- + Cada modulo tem responsabilidade unica (SRP), <= 220 linhas.
- + Trocar persistencia (`_state`), git (`_git_ops`) ou clock (`_clock`)
  e isolado - DIP via importacao + monkeypatch.
- + Constantes centralizadas: politica PT/EN futura, mensagem nova ou
  rename de status fica num arquivo so.
- + `lock_api` finalmente reutilizado: lock_task_files passa por
  `add_lock`, respeita `lock-ignore.txt`, normaliza paths, valida
  path-traversal. Bug latente corrigido.
- + 63 testes unitarios viaveis (antes 4 smoke). Pyramide saudavel.
- - 17 arquivos novos em `core/src/` aumentam a "lista de arquivos" no
  IDE. Compensado pelo tamanho menor de cada um e pela busca por nome.
- - `dist/bin/` agora tem 19 arquivos ao inves de 3. Os 16 a mais sao
  pequenos (todos < 7KB). Renderer cobre `--check` integrado.
- - Test de smoke precisou ser atualizado para copiar todo o pacote ao
  sandbox; install test continuou inalterado pois ja consumia `dist/`.

## Alternativas consideradas

- **A) Manter monolito com comentarios de secao.** Custo zero, mas nao
  resolve nenhuma das dores. Rejeitada.
- **B) Pacote Python real (`core/src/ai_process/`) com `__init__.py`.**
  Tornaria o entry-point `python -m ai_process`. Quebraria o jeito
  documentado `python core/src/ai.py` e exigiria renomear referencias
  em dezenas de docs. Rejeitada por custo de migracao.
- **C) Split parcial (so extrair docs_hook e lock_task_files).**
  Reduziria pra ~750 linhas. Resolveria 2 problemas de 5. Rejeitada por
  ficar pela metade.

## Links

- [Auditoria F-014](../auditorias/F-014-core.md) - levantamento que
  motivou o split.
- [F-014 validacao](../auditorias/F-014-validacao.md) - relatorio do
  resultado.
- [ADR-0001](0001-script-fonte-da-verdade.md) - script como fonte unica
  continua valido; agora o script e um pacote.
