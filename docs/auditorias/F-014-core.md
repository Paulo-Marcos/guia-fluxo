# Auditoria F-014 - core/

Acompanhamento estruturado da auditoria de `core/` para mapear features, issues e backlog.

- **Task:** [F-014](../../FEATURES.md) - Auditoria estruturada de core/ para mapear features, issues e backlog
- **Inicio:** 2026-06-02
- **Status geral:** Levantamento concluido (7/7 etapas). Aguardando avaliacao do dev + disparo em lote (etapa 8/tracker).
- **Criterio de saida:** lista consolidada de candidatos aprovada pelo dev, todos abertos como F-/I-/B- via CLI, doc atualizado com o destino final de cada item.

## Como retomar (importante)

O dev quer reavaliar a maior parte dos candidatos **depois de iniciar as refatoracoes** - muita coisa pode mudar de forma quando o codigo melhorar. Por isso:

- Cada candidato tem **STATUS** explicito na tabela:
  - `proposto` - levantado na auditoria, aguardando decisao do dev.
  - `aprovado` - dev confirmou que vira F-/I-/B-, mas ID ainda nao foi atribuido (sera aberto no disparo em lote da etapa 8).
  - `aberto` - ja virou F-NNN/I-NNN/B-NNN, ID preenchido na coluna correspondente.
  - `rejeitado` - dev decidiu nao tratar.
- **Como retomar:** abrir este doc, ir na secao "Consolidado" no final, filtrar por `proposto`. Para cada um, o dev decide e atualiza o STATUS. Approvados sao abertos via CLI no fim, com ID anotado.
- **Quando reavaliar:** o dev planeja revisitar a lista DEPOIS de pelo menos uma rodada de refatoracao (Q2/opcao B do manifest). Achados que dependem do estado atual do codigo podem ficar obsoletos - por isso a coluna STATUS e nao a coluna ID e a fonte de verdade durante a auditoria.

## Como ler este doc

Cada etapa segue o mesmo formato:

- **Proposito** - o que o arquivo/funcionalidade existe pra fazer, quem le, quem depende, posicao na arquitetura.
- **Perguntas estruturais** - duvidas do dev sobre design (formato, layout, escopo), respondidas com base em codigo + ADRs.
- **Achados** - lista numerada, cada item com path:linha + excerto + onde corrigir.
- **Candidatos** - mesma numeracao dos achados, com classificacao proposta (`[FEATURE]`, `[ISSUE]`, `[BACKLOG]`, `[NO-OP]`) e ID atribuido depois da aprovacao.

No final, a secao **Consolidado** vira a fonte de verdade pro disparo em lote.

## Etapas

| # | Area | Status |
|---|---|---|
| 1 | `core/manifest/manifest.yaml` | Concluida (13 candidatos levantados; Q2 aprovada, restantes propostos) |
| 2 | `core/src/ai.py` | Em analise |
| 3 | `core/bin/ai.ps1` | Concluida (10 candidatos levantados, todos propostos) |
| 4 | `core/build/render-skills.py` | Concluida (17 candidatos, 6 compostos com etapas 1 e 3) |
| 5 | `core/lock/check-lock.py` | Concluida (15 candidatos, 1 composto com etapa 2) |
| 6 | `core/hooks/commit-msg` + `core/templates/.githooks/commit-msg` | Concluida (9 candidatos, 4 compostos) |
| 7 | `core/templates/features/*` | Concluida (9 candidatos, 5 compostos) |

---

## Etapa 1 - `core/manifest/manifest.yaml`

### Proposito

Fonte unica de verdade dos *skills* do pack. **Nao e config runtime** - e **input** do gerador `core/build/render-skills.py`.

Declara, por verbo:
- **description** - string que cada host (Claude Code, Codex, Antigravity) usa pra decidir QUANDO carregar essa skill. Diferenciacao entre descriptions e o que evita trigger collision (F-003).
- **targets.agent_skill.body** - markdown que vira `dist/.agents/skills/ai-<verbo>/SKILL.md` (Codex + Antigravity).
- **targets.claude_skill.body** - markdown que vira `dist/skills/<verbo>/SKILL.md` (Claude Code, namespace `ai:`).

Pipeline:

```
core/manifest/manifest.yaml          <- FONTE (este arquivo)
        |
        v  core/build/render-skills.py
        |
   +----+--------------------------+
   v                               v
dist/skills/<verbo>/SKILL.md   dist/.agents/skills/ai-<verbo>/SKILL.md
   |                               |
   v                               v
Claude Code (/ai:feature)      Codex + Antigravity (/use ai-feature)
```

- *Quem le este arquivo em runtime:* ninguem. So `render-skills.py` em build time.
- *De quem este arquivo depende implicitamente:* contrato das flags do `core/src/ai.py`. Bodies citam `--context`, `--lock`, etc. Se o CLI muda flag, body fica errado sem aviso.

### Perguntas estruturais

#### Q1 - Por que YAML?

ADRs verificados:
- [`docs/adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md) documenta o **layout** do plugin mas nao justifica YAML.
- [`docs/adr/0003-json-maquina-markdown-humano.md`](../adr/0003-json-maquina-markdown-humano.md) explicitamente **rejeita YAML** como unica fonte pra estado de tasks ("whitespace-sensitive, diff ruidoso em arrays"). Era outro contexto - dados de processo. Nao cobre source de geracao.
- **Nao existe ADR justificando YAML aqui. Decisao tacita.**

Por que YAML funciona neste caso:
1. **Multi-line strings via `|` (block literal).** Bodies sao markdown longo (10-30 linhas com code fences). JSON exigiria escape `\n` em toda linha. Inviavel.
2. **PyYAML ja e dependencia do projeto** (`check-lock.py`, `ai.py docs-check`).
3. **Padrao de fato no ecossistema** (frontmatter SKILL.md, GitHub Actions, plugin manifests).

Onde YAML morde - evidencia real no projeto:
- **Whitespace-sensitive.** Indentacao errada quebra estrutura sem erro obvio.
- **`on:` vira `True` em PyYAML 1.1.** **Ja virou bug** - ha workaround defensivo em [`core/src/ai.py:716-720`](../../core/src/ai.py).
- **Sem schema.** `yaml.safe_load` + `dict.get(...)` em runtime. Erros tardios.

Alternativas reais:

| Formato | Multi-line | Schema | DX para bodies markdown |
|---|---|---|---|
| **YAML (atual)** | Bom (`\|`) | Manual | Familiar mas com pegadinhas |
| **JSON** | Ruim (escapes) | JSON Schema | Inviavel |
| **TOML** | Bom (`"""`) | Manual | Verboso pra hierarquia profunda |
| **Markdown por verbo + frontmatter** | Nativo | Frontmatter YAML | Cada verbo e um arquivo |

**Recomendacao:** manter YAML, mas atacar Q2 + Q3 em paralelo. Ganho de mudar formato puro e baixo; ganho de mudar layout (Q2) e alto.

> **Candidato derivado:** `[BACKLOG]` ADR (0007) documentando escolha de YAML, anti-padroes conhecidos (caso `on:`), e quando reconsiderar.

#### Q2 - Por que arquivo unico? Vale separar?

Estado atual: 422 linhas. 7 verbos x 2 targets = 14 bodies + metadata. O renderer ([`core/build/render-skills.py:87-91`](../../core/build/render-skills.py)) le **um path hardcoded** e itera em memoria em [`render-skills.py:137`](../../core/build/render-skills.py). **Mudar pra N arquivos e refactor pequeno no renderer.**

Tres designs concorrentes:

**A) 1 YAML por verbo:**
```
core/manifest/
  feature.yaml      (~40 linhas)
  issue.yaml        (~40)
  ...
  ai-process.yaml   (~120)
```
- + Cada arquivo bounded. Diff escopado. Adicionar verbo = criar arquivo.
- - Perde vista panoramica. Convencao de ordem implicita.

**B) Index YAML + bodies em markdown puro:**
```
core/manifest/
  manifest.yaml          (~80 linhas - so estrutura: verbo -> description -> caminhos)
  bodies/
    feature.agent.md
    feature.claude.md
    ...
```
- + Estrutura validavel concentrada (todas as 7 descriptions juntas - colisao fica visualmente obvia).
- + Bodies em markdown puro: preview, syntax highlight, diff limpo, **sem pegadinhas YAML**.
- + `shared_body` natural - dois targets podem apontar pro mesmo arquivo.
- - 1 verbo = 1+2 arquivos. Mais indirecao.

**C) Pasta por verbo:**
```
core/manifest/verbs/
  feature/skill.yaml, feature/agent.md, feature/claude.md
  ...
```
- + Tudo do verbo no mesmo lugar. Lock granular possivel.
- - 3 arquivos x 7 verbos = 21+ arquivos. Profundidade maior.

Comparativo:

| Aspecto | A | **B (recomendada)** | C | Atual |
|---|---|---|---|---|
| Linhas por arquivo | 30-120 | 10 + bodies | 5-15 | **422** |
| Validar 1 verbo | 1 file | 1+2 files | 3 files | scroll em 422 |
| Diff PR | Bom | Otimo | Otimo | Ruim |
| Vista panoramica | Media | Boa (index) | Ruim | Boa |
| Refactor renderer | Pequeno | Medio | Pequeno | - |
| `shared_body` natural | Dificil | **Trivial** | Trivial | Dificil |

**Recomendacao:** **Opcao B.** Resolve Q2, Q3 e viabiliza o achado #5 (shared_body) em um movimento.

> **Candidato derivado:** `[FEATURE]` migrar `core/manifest/manifest.yaml` para layout B (index + bodies markdown). Inclui refactor no renderer.

#### Q3 - Tamanho dificulta validar

Sim. Resposta principal: **opcao B da Q2.** Mas tem 4 camadas complementares de validacao independentes do split:

1. **Schema do manifest.** Hoje: `yaml.safe_load` + `dict.get` em runtime. Erros so ao tentar gerar. Schema com `jsonschema` ou `pydantic` valida no `--check` antes.
2. **Body vs CLI introspectado.** O `argparse` em `core/src/ai.py` e introspectavel. Da pra extrair flags reais de cada subcomando e checar se bodies so citam flags que existem. Pega o achado #1 antes de virar drift.
3. **Manifest <-> `marketplace.json`.** Verbo no manifest deveria aparecer em `dist/.claude-plugin/marketplace.json`. Sem check hoje.
4. **Limite/similaridade de descriptions.** Reincidencia do trigger collision (F-003) - duas descriptions muito parecidas voltam o problema.

> **Candidato derivado:** ja capturado como achado #7 abaixo.

### Achados (com localizacao)

| # | Onde esta hoje (path:linha) | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | [`manifest.yaml:177-186`](../../core/manifest/manifest.yaml) feature claude_skill: `.\core\bin\ai.ps1 feature "$ARGUMENTS"`. CLI parser [`ai.py:55-58`](../../core/src/ai.py) declara `title`, `--context`, `--origin`. Mesmo padrao em issue (`202-214`), ready (`317-331`), finish (`358-394`), promote (`279-300`). | Body omite flags relevantes; agente esquece de passar `--context`, `--run-tests`, `--lock-description`, `--docs-checked`. | Pontual: atualizar bodies. Duradouro: smoke test (achado #7). |
| 2 | CLI subcomandos sem shim: `docs-check` ([`ai.py:104-114`](../../core/src/ai.py)), `doctor` ([`ai.py:145-146`](../../core/src/ai.py)), `render` ([`ai.py:148-151`](../../core/src/ai.py)). Lock CLI inteiro ([`check-lock.py`](../../core/lock/check-lock.py)) sem shim. | 6 capacidades do pack sem skill; dev precisa lembrar do path completo. | Adicionar verbos `docs-check`, `doctor`, `render`, `lock`, `unlock`, `audit` em `manifest.yaml`. |
| 3 | `feature/issue/backlog/ready` agent_skill **tem** "Then continue using `ai-process`." no fim. `promote` (~273-277) e `finish` (~349-357) agent_skill **nao tem**. `status` (~408) tambem nao mas e coerente (read-only). | Justo promote/finish, os 2 fluxos mais complexos, nao recarregam contexto. | Adicionar rodape em promote e finish agent_skill. |
| 4 | Mistura PT/EN. Bodies do `ai-process` 100% EN; outros bodies misturam EN com nomes de status em PT ("Aguardando validacao"). | Sem politica definida. | Decidir politica, aplicar uniformemente. |
| 5 | [`manifest.yaml:162-172`](../../core/manifest/manifest.yaml) (feature agent_skill, 7 linhas) vs `173-186` (feature claude_skill, 9 linhas): ~70% conteudo semantico igual. Difere so metodo de rename + sintaxe `$ARGUMENTS`. | Duplicacao multiplica manutencao; flag nova exige editar 14 bodies. | `shared_body` no schema do manifest - viabilizado pela opcao B da Q2. |
| 6 | `ai-process` description em [`manifest.yaml:23`](../../core/manifest/manifest.yaml) tem ~440 chars com prefixo "REFERENCE/BACKGROUND ONLY". Outros 6 seguem padrao ("PRIMARY TRIGGER", "DEFER-AND-PARK", "EVALUATE-AND-CONVERT", "HANDOFF", "CLOSE", "READ-ONLY") instituido em F-003. | Padrao de prefixo so vive na PR de F-003 e no commit log. Proximo editor pode quebrar. | ADR novo (0007) OU comentario inline no topo de `manifest.yaml`. |
| 7 | `render-skills.py --check` ([`render-skills.py:215-221`](../../core/build/render-skills.py)) so compara saida com disco. Nao valida cobertura de targets, flags do body vs CLI real, sincronia com marketplace.json, limite/similaridade de description. | Drift silencioso fica invisivel ate alguem ler o body errado. | Estender `--check` em `render-skills.py` com as 4 validacoes. |
| 8 | Body do `promote` (`279-300` claude, `254-278` agent) so diz "include `--worktree`". CLI ([`ai.py:369-385`](../../core/src/ai.py) `attach_worktree`) cria branch `codex/<slug>` e path `.claude/worktrees/<slug>`. | Dev nao sabe nome da branch que vai virar. | Adicionar nota no body do promote (ambos targets). |
| 9 | So o body do `ai-process` cita fallback `python core/src/ai.py`. Os 6 verbos triggers usam apenas `.\core\bin\ai.ps1`. | Dev sem PowerShell fica orfao. | Cada body trigger pode mostrar a forma cross-platform. |
| 10 | [`ai.py:325-329`](../../core/src/ai.py) `cmd_backlog_list` itera sem ordem nem filtro. | Backlog tem 0 itens - nao e problema hoje. | Esperar crescer. |
| 11 | Bodies usam `$ARGUMENTS` literal em comandos PowerShell. CC substitui ANTES do PS ver. **Risco real:** argumento com `"` quebra parsing PS. Ex: `/ai:feature "Bug com "aspas""` vira `.\core\bin\ai.ps1 feature "Bug com "aspas""`, que PS le como multiplas strings. | Caso de borda nunca exercitado. Pode falhar silencioso ou explodir feio. | Testar caso de borda; documentar limitacao ou usar single-quotes/call operator. |

### Candidatos

Inclui 3 candidatos derivados das perguntas estruturais (Q1, Q2, Q3) e os 11 achados.

| # | Classificacao proposta | Resumo curto | STATUS | ID final |
|---|---|---|---|---|
| Q1 | `[BACKLOG]` | ADR 0007 documentando escolha de YAML pra manifest, caso `on:->True`, quando reconsiderar formato. | proposto | - |
| **Q2** | **`[FEATURE]`** | **Migrar `core/manifest/manifest.yaml` para layout B (index YAML + bodies markdown em `bodies/`). Inclui refactor do renderer.** | **aprovado** | - |
| 1 | `[ISSUE]` | Bodies do `claude_skill` (feature/issue/ready/finish/promote) omitem flags relevantes do CLI; alinhar com agent_skill. | proposto | - |
| 2 | `[FEATURE]` | Adicionar 6 verbos shim no manifest: `/ai:doctor`, `/ai:render`, `/ai:docs-check`, `/ai:lock`, `/ai:unlock`, `/ai:audit`. | proposto | - |
| 3 | `[ISSUE]` | `promote` e `finish` (agent_skill) nao trazem rodape "Then continue using `ai-process`". | proposto | - |
| 4 | `[BACKLOG]` | Decidir politica PT vs EN para skill bodies e aplicar uniformemente. | proposto | - |
| 5 | `[BACKLOG]` | Permitir `shared_body` + overrides por target no manifest. Combina com Q2/B. | proposto | - |
| 6 | `[BACKLOG]` | Documentar prefixos "PRIMARY TRIGGER / DEFER-AND-PARK / EVALUATE-AND-CONVERT" em ADR ou comentario inline. | proposto | - |
| 7 | `[FEATURE]` | Smoke tests do manifest no `render-skills.py --check`: cobertura de targets, validacao de flags vs CLI, sincronia com marketplace.json, limite/similaridade de description. | proposto | - |
| 8 | `[ISSUE]` | Body do `promote` (claude e agent_skill) deve mencionar que `--worktree` cria branch `codex/<slug>` e path `.claude/worktrees/<slug>`. | proposto | - |
| 9 | `[BACKLOG]` | Documentar fallback `python core/src/ai.py <verbo>` em cada skill body. | proposto | - |
| 10 | `[NO-OP]` | "backlog list sem ordem/paginacao" - esperar crescer. | proposto | - |
| 11 | `[ISSUE]` | Confirmar/testar substituicao de `$ARGUMENTS` em bodies PS com argumentos contendo aspas. | proposto | - |

---

## Etapa 2 - `core/src/ai.py`

### Proposito

**O motor portavel da CLI inteira do AI process.** E o coracao funcional do pack - todos os outros arquivos em `core/` ou sao wrappers (`ai.ps1`), geradores que o copiam (`render-skills.py`), ou ferramentas auxiliares com escopo bem mais estreito (`check-lock.py`, hooks).

**O que esse arquivo faz:**
- Implementa **todos** os subcomandos: `init`, `feature`, `issue`, `status`, `ready`, `finish`, `validate` (deprecated), `backlog (add/list/promote)`, `promote`, `doctor`, `render`, `docs-check`
- Gerencia estado em `.ai/*.json` (tasks, backlog, current-task, chat-title, process config)
- Mantem `FEATURES.md` (espelho humano agregado) sincronizado
- Escreve relatorios em `.ai/reports/<task>-<event>-<timestamp>.md`
- Escreve `features/registry.yaml` (locks) - **paralelo ao `check-lock.py`** (ver Q3)
- Roda git: changed files, staged files, commit, worktree create/remove
- Executa o hook de docs (F-010): carrega `.ai/docs-map.yaml`, lista candidatos, bloqueia `finish` sem revisao

**Quem invoca:**
- [`core/bin/ai.ps1`](../../core/bin/ai.ps1) - wrapper PowerShell (caso primario no Windows)
- `dist/bin/ai.py` (copia byte-a-byte feita por [`render-skills.py:174-178`](../../core/build/render-skills.py)) - quando o pack roda como plugin no consumidor
- `python core/src/ai.py <cmd>` direto - fallback documentado
- Indiretamente: **todos** os bodies do manifest chamam o CLI

**De que depende:**
- stdlib: `argparse`, `json`, `re`, `subprocess`, `pathlib`, `datetime`, `fnmatch`, `shutil`
- **Externos opcionais:** `PyYAML` (so pra `docs-check`), `git` no PATH (para varias operacoes)
- **Implicitamente** do contrato de schema de `.ai/*.json` (sem versionamento), do `FEATURES.md` (regex de parser), e de `.ai/docs-map.yaml`

### Mapa do arquivo (965 linhas)

| Linhas | Bloco | Responsabilidade |
|---|---|---|
| 1-37 | header + constants | docstring, paths fixos, regex |
| 40-153 | `main` + `build_parser` | argparse de todos os subcomandos |
| 156-171 | helpers de args | `add_task_args`, `add_promote_args` |
| 174-408 | `cmd_*` handlers | 13 handlers de subcomando |
| 411-435 | `default_process` | schema embutido do process.json |
| 438-481 | task creation helpers | `new_task`, `next_task_id`, `next_backlog_id`, `number_from_id`, `numbers_from_features` |
| 484-523 | task lookup/save + merge_list | CRUD em memoria |
| 526-545 | features.md upsert | regex + write |
| 547-588 | rendering | `render_features_block`, `markdown_list`, `task_kind_label`, `run_validation_commands` |
| 591-624 | git + worktree | `commit_task`, `cleanup_task_worktree` |
| 626-672 | lock + git changed files | `lock_task_files`, `git_changed_files` |
| **674-852** | **docs hook (F-010)** | `load_docs_map`, `compute_docs_candidates`, `trigger_reason`, `ensure_docs_review_ok`, `build_docs_review_record`, `print_docs_block`, `cmd_docs_check` |
| 855-905 | task output | `write_report`, `print_task_created`, `chat_title`, `status_tag`, `current_task_payload`, `set_current_task`, `print_chat_title` |
| 908-960 | generic helpers | `git_staged_files`, `git_command`, `yaml_string`, `slugify`, `write_if_missing`, `read_json`, `write_json`, `read_text`, `relative`, `today` |

### Perguntas estruturais

#### Q1 - 965 linhas em arquivo unico: split em modulos e viavel?

**Hoje:** tudo num arquivo so, sem testes. Dificulta:
- Localizar funcionalidade ("onde mexer a logica de worktree?" exige ctrl+F)
- Revisar PRs (mudanca pequena se perde no scroll)
- Reutilizar (nao da pra importar lock logic em outro lugar sem importar argparse setup junto)
- Testar (impossivel mockear `subprocess` ou `Path` em granularidade de funcao sem refactor)

**Split sugerido:**
```
core/src/
  ai.py                         # main() + build_parser() apenas (~150 linhas)
  cli/
    feature_issue.py            # cmd_create_task, args helpers
    backlog.py                  # cmd_backlog_*, cmd_promote
    lifecycle.py                # cmd_status, cmd_ready, cmd_finish, cmd_validate
    docs.py                     # cmd_docs_check
    meta.py                     # cmd_init, cmd_doctor, cmd_render
  domain/
    tasks.py                    # new_task, next_id, find/save, current
    features_md.py              # upsert, render_block, markdown_list
    docs_hook.py                # load_docs_map, compute_candidates, ensure_review
    git_ops.py                  # git_command, staged/changed, commit_task, worktree
    locks.py                    # PONTE para check-lock.py (nao duplicar)
  io/
    state.py                    # read_json, write_json, write_if_missing
```

**Riscos:**
- Mexer onde o pack inteiro escora. Precisa de smoke test antes.
- `dist/bin/ai.py` e copia byte-a-byte de `ai.py` - split exigiria que `render-skills.py` empacote os modulos juntos OU mantenha um `ai.py` flat so para o dist.

**Recomendacao:** `[FEATURE]` se o dev topa o esforco; senao, `[BACKLOG]` para quando a dor doer mais. Sugerido comecar por extrair `docs_hook.py` (174 linhas autonomas) como prova de conceito.

#### Q2 - `validate` deprecated mas exposto: remover ou warning?

CLI ainda aceita `validate` ([linhas 116-123, 287-305](../../core/src/ai.py)). Manifest nao tem skill. CLAUDE.md diz "Nao use validate como skill". Mas o subcomando existe.

**Opcoes:** A) Remover; B) Warning explicito; C) Manter silencioso (estado atual).

**Recomendacao:** B agora, A daqui a 2-3 versoes.

#### Q3 - `lock_task_files` reimplementa `check-lock.py`: extrair lock module compartilhado?

Em [`ai.py:626-658`](../../core/src/ai.py), `lock_task_files` escreve `features/registry.yaml` **a mao** via concat de strings. Enquanto [`check-lock.py:79-101`](../../core/lock/check-lock.py) ja tem `_load_data`, `_save_locks`, `_load_lock_ignore`, `_norm`.

**Consequencias:**
- `lock_task_files` **nao respeita `lock-ignore.txt`** - pode travar `.gitignore`
- Nao normaliza paths via `_norm()` - Windows backslash vira mismatch
- Sempre bloqueia todas as 4 operacoes (nao suporta `operations: [add]`)
- Schema vinculado por convencao, nao por codigo compartilhado

**Recomendacao:** `[FEATURE]` - refatorar `check-lock.py` para expor modulo importavel. Combina com Q1 (cria oportunidade do `core/src/domain/locks.py`).

#### Q4 - `commit_task` nao pre-valida locks: pre-flight check?

[`commit_task` (591-601)](../../core/src/ai.py) faz `git add` + `git commit -m "..."`. Mensagem fixa. Se task tocou arquivo travado, hook `commit-msg` bloqueia. ai.py nao sabe sugerir `[unlock:<id>]`.

**Recomendacao:** `[ISSUE]` - `finish` chama `check-lock.py check <files>` antes de commit; aborta com mensagem clara ou aceita flag de unlock.

### Achados (com path + linha)

| # | Onde esta (path:linha) | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | [`ai.py:271` + `ai.py:280`](../../core/src/ai.py) - `cleanup_task_worktree` chamado 2x em `cmd_finish` | Primeira chamada antes de `save_task`/commit, segunda apos. Segunda quase sempre vira no-op. Leftover de refactor. | Remover a primeira (linha 271). |
| 2 | [`ai.py:332-349`](../../core/src/ai.py) `cmd_promote` | `pop_item` grava backlog (337) ANTES de criar task (338). Se `create_promoted_task` ou `attach_worktree` falhar, item se perde. | Gravar backlog so apos task confirmada. |
| 3 | [`ai.py:591-601`](../../core/src/ai.py) `commit_task` | Mensagem fixa. Sem hook pra enriquecer. | Capturado em Q4. |
| 4 | [`ai.py:595-598`](../../core/src/ai.py) `commit_task` checa `git_staged_files()` vs `set(files)` | Compara paths literais; Windows pode dar mismatch backslash vs slash. | Normalizar via `Path(...).as_posix()`. |
| 5 | [`ai.py:484-492`](../../core/src/ai.py) `find_task_or_current` | Falha com "Task not found: X" sem listar IDs validos. | Mostrar 5 tasks recentes. |
| 6 | [`ai.py:527-528`](../../core/src/ai.py) `upsert_features_entry` | Cria FEATURES.md silenciosamente. Hardcoded estrutura inicial. | Validar contra docs-map ou tornar configuravel. |
| 7 | [`ai.py:448`](../../core/src/ai.py) `new_task` | Hardcoded `modifiedFiles: ["FEATURES.md"]`. | Mover para config ou injetar dinamicamente. |
| 8 | [`ai.py:27-35`](../../core/src/ai.py) - constants | Paths fixos. Consumidor nao customiza. | ADR/doc "convention over config" OU configuravel. |
| 9 | [`ai.py:268-280`](../../core/src/ai.py) `cmd_finish --no-commit` | "Dry close" ainda remove worktree. | Skip cleanup quando `not commit_requested`. |
| 10 | [`ai.py:388-395`](../../core/src/ai.py) `cmd_doctor` | So checa 4 arquivos `.ai/`. | Estender (manifest, PyYAML, git, render --check, dist). |
| 11 | [`ai.py:50-153`](../../core/src/ai.py) | NENHUM subcomando `tasks list/show/filter`. | Adicionar subcomandos de query. |
| 12 | [`ai.py:599`](../../core/src/ai.py) `commit_task` | Se git nao esta no PATH, FileNotFoundError generico. | Try/except com mensagem clara. |
| 13 | [`ai.py:369-385`](../../core/src/ai.py) `attach_worktree` | Cria branch sem checar existencia; git erro confuso. | `git rev-parse --verify` antes. |
| 14 | [`ai.py:547-574`](../../core/src/ai.py) | Strings hardcoded PT-BR ("Aguardando validacao", "Nenhuma.", etc.) | Combina com Etapa 1.4 (politica PT/EN). |
| 15 | Todo o arquivo | NENHUM teste automatizado pro CLI. | Pytest com smoke tests por subcomando. |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | `[FEATURE]` ou `[BACKLOG]` | Split de `core/src/ai.py` em modulos. | proposto | - |
| Q2 | `[ISSUE]` | `validate` com warning explicito; remocao em N+2. | proposto | - |
| Q3 | `[FEATURE]` | Extrair lock logic de `check-lock.py` em modulo importavel. | proposto | - |
| Q4 | `[ISSUE]` | `finish` pre-valida locks antes de commit. | proposto | - |
| 1 | `[ISSUE]` | Remover `cleanup_task_worktree` duplicado em `cmd_finish`. | proposto | - |
| 2 | `[ISSUE]` | `cmd_promote` deve gravar backlog so apos task confirmada. | proposto | - |
| 3 | (=Q4) | - | - | - |
| 4 | `[ISSUE]` | Normalizar paths em `commit_task` (Windows backslash). | proposto | - |
| 5 | `[BACKLOG]` | Erro de `find_task_or_current` lista IDs recentes. | proposto | - |
| 6 | `[BACKLOG]` | `upsert_features_entry` configuravel; nao cria sem aval. | proposto | - |
| 7 | `[BACKLOG]` | Remover hardcoded `FEATURES.md` em `new_task`. | proposto | - |
| 8 | `[BACKLOG]` | ADR/doc "convention over config" pros paths fixos. | proposto | - |
| 9 | `[ISSUE]` | `cmd_finish --no-commit` nao remove worktree. | proposto | - |
| 10 | `[FEATURE]` | Estender `cmd_doctor`. | proposto | - |
| 11 | `[FEATURE]` | `tasks list/show/filter` subcomandos. | proposto | - |
| 12 | `[ISSUE]` | Mensagem clara quando git nao esta no PATH. | proposto | - |
| 13 | `[ISSUE]` | `attach_worktree` pre-checa branch. | proposto | - |
| 14 | (combina com Etapa 1.4) | - | - | - |
| 15 | `[FEATURE]` | Pytest com smoke tests. | proposto | - |

---

## Etapa 3 - `core/bin/ai.ps1`

### Proposito

**Wrapper PowerShell que resolve um interpretador Python valido e chama `core/src/ai.py` repassando os argumentos.** E o "ponto de entrada amigavel" no Windows - em vez de o dev digitar `python core\src\ai.py feature ...`, ele digita `.\core\bin\ai.ps1 feature ...`.

**O que esse arquivo faz:**
- Recebe argumentos arbitrarios via `[Parameter(ValueFromRemainingArguments = $true)]` (linhas 1-4)
- Tenta resolver um interpretador Python de uma lista de **7 candidatos em ordem fixa** (linhas 29-50)
- Filtra o **stub do Microsoft Store** (linhas 8-27): `Test-Python` verifica que `python --version` realmente roda
- Trata o caso especial do **launcher `py`** (linhas 16-17, 55-57): usa `py -3` para garantir Python 3
- Invoca `core/src/ai.py` com `& $python $script @Args` (linhas 55-60)
- Propaga o exit code com `exit $LASTEXITCODE` (linha 62)

**Ordem de candidatos** (linhas 33-41):
1. `$env:AI_PROCESS_PYTHON` (env override explicito)
2. `..\..\.venv\Scripts\python.exe` (venv local no root do repo)
3. `python` (PATH)
4. `python3` (PATH)
5. `py` (Windows launcher -> `py -3`)
6. `$env:LOCALAPPDATA\Programs\Python\Python313\python.exe` (Python 3.13 per-user install)
7. `$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` (Codex bundled Python)

**Quem invoca:**
- Todos os bodies do manifest (todas as 7 skills de trigger)
- Dev digitando manualmente no Windows
- **Adaptado** e copiado para `dist/bin/ai.ps1` por [`render-skills.py:149-161`](../../core/build/render-skills.py) com substituicao `..\src\ai.py` -> `ai.py` (layout flat no plugin)

**De que depende:**
- PowerShell (versao nao especificada - ver Q1)
- Python disponivel por **alguma** das 7 vias

### Perguntas estruturais

#### Q1 - Por que so wrapper Windows? Falta `core/bin/ai` (POSIX)?

O pack e distribuido como plugin que roda em qualquer plataforma - `dist/bin/ai` (POSIX shim bash) e **gerado** por [`render-skills.py:80-84`](../../core/build/render-skills.py). Mas no repo-mae nao existe wrapper POSIX. Dev no Mac/Linux contribuindo no `ai-process-pack` precisa rodar `python core/src/ai.py <cmd>` direto OU primeiro gerar `dist/bin/ai`.

**Recomendacao:** `[FEATURE]` - criar `core/bin/ai` (shim POSIX simetrico ao `dist/bin/ai`). Custo baixissimo, simetria util pra devs em Mac/Linux do proprio pack.

#### Q2 - Resolucao de Python fragil: estrategia mais robusta?

Problemas concretos na lista de 7 candidatos:
- **`Python313` hardcoded** (linha 30) - quebra em Python 3.14, 3.15 silencioso
- **Path Codex especifico** (linha 32) - vinculado ao branding `codex-primary-runtime`
- **`.venv` unico path** (linha 31) - assume venv no root; ignora `venv\`, `env\`, etc.
- **Sem deteccao de venv ativo** - se `$env:VIRTUAL_ENV` setado, deveria ser primeira escolha

**Estrategia alternativa em camadas:**
1. `$env:AI_PROCESS_PYTHON` (override explicito)
2. `$env:VIRTUAL_ENV\Scripts\python.exe` (venv ativo) - novo
3. `py -3` (Windows launcher universal)
4. `python3` / `python` (PATH)
5. Paths conhecidos como ultimo recurso, **descobertos via glob** (`Python3*` em vez de `Python313`)

**Recomendacao:** `[FEATURE]` - refactor de `Resolve-Python`. Resolve achados 1, 2, 3 de uma vez.

#### Q3 - Por que wrapper PS em vez de `ai.py` executavel direto?

Wrapper existe porque Windows nao associa `.py` a Python por padrao sem ajuste no PATHEXT, e dev digita `ai.ps1` em vez de `python core\src\ai.py`.

**Alternativa complementar:** `core/bin/ai.cmd` (shim para `cmd.exe`):
```cmd
@py -3 "%~dp0..\src\ai.py" %*
```
Roda em **cmd.exe** e PS sem syntax PS.

**Recomendacao:** `[BACKLOG]` - util mas nao urgente.

### Achados (com path + linha)

| # | Onde esta (linha) | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | linha 30: `Python313` literal | Quebra em Python 3.14+ silencioso. | Glob `Python3*` ou usar `py -3` mais cedo. (Em Q2.) |
| 2 | linha 32: `codex-primary-runtime` | Vinculo a branding Codex; risco se Codex mudar layout. | Tornar opcional ou descobrir via env. (Em Q2.) |
| 3 | linha 31: `..\..\.venv\Scripts\python.exe` | Unico path de venv; ignora `venv\`, `env\`. | Detectar `$env:VIRTUAL_ENV` primeiro. (Em Q2.) |
| 4 | linha 49: `throw "Python not found..."` | Mensagem generica; nao lista paths tentados nem sugere instalacao. | Enriquecer diagnostico. |
| 5 | linha 22: `return $LASTEXITCODE -eq 0` | Verifica que rodou, mas **nao valida versao >= 3.10**. Python 2.7 passaria. | Parsear `--version` e checar major.minor. |
| 6 | linha 3: `[string[]] $Args` | Param shadows `$Args` automatico do PS. | Renomear para `$Arguments` ou `$CliArgs`. |
| 7 | Wrapper inteiro | Sem flag `--debug` / `-Verbose` que imprima qual Python foi escolhido. | Adicionar `-Verbose` que mostra candidato + versao. |
| 8 | linha 53 | Nao pre-checa que `core/src/ai.py` existe; se sumir, Python da erro generico. | `if (-not (Test-Path $script)) { throw ... }`. |
| 9 | Wrapper inteiro | Sem `core/bin/ai` POSIX equivalente. | (Em Q1.) |
| 10 | Wrapper inteiro | Sem `core/bin/ai.cmd` para cmd.exe. | (Em Q3.) |
| 11 | linhas 16-17 + 55-57 | Logica especial pra `py` duplicada. | Centralizar em `Invoke-PythonScript`. |
| 12 | linha 6: `$ErrorActionPreference = "Stop"` | Comportamento correto sem comentario explicativo. | Comentario inline. |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | `[FEATURE]` | Criar `core/bin/ai` (shim POSIX bash) simetrico ao `dist/bin/ai`. | proposto | - |
| Q2 | `[FEATURE]` | Refactor `Resolve-Python` com estrategia em camadas. | proposto | - |
| Q3 | `[BACKLOG]` | `core/bin/ai.cmd` para invocacao a partir de cmd.exe. | proposto | - |
| 4 | `[ISSUE]` | Mensagem de erro de Python ausente lista paths tentados + sugestao. | proposto | - |
| 5 | `[ISSUE]` | `Test-Python` valida versao >= 3.10. | proposto | - |
| 6 | `[BACKLOG]` | Renomear param `$Args` -> `$Arguments` ou `$CliArgs`. | proposto | - |
| 7 | `[BACKLOG]` | Flag `-Verbose` que imprime Python selecionado. | proposto | - |
| 8 | `[ISSUE]` | Pre-checar existencia de `core/src/ai.py`. | proposto | - |
| 11 | `[BACKLOG]` | Centralizar logica especial de `py` em funcao unica. | proposto | - |
| 12 | `[BACKLOG]` | Comentario inline explicando `$ErrorActionPreference = "Stop"`. | proposto | - |

---

## Etapa 4 - `core/build/render-skills.py`

### Proposito

**O gerador que converte fonte unica (`core/`) em arvore distribuivel (`dist/`).** E a ponte entre source-of-truth (manifest + engine + wrapper + templates) e os artefatos que o consumidor recebe quando instala o plugin.

**O que produz:**
- `dist/skills/<verb>/SKILL.md` - Claude Code (sem prefixo `ai-`, namespace `ai:` ja qualifica)
- `dist/.agents/skills/ai-<verb>/SKILL.md` - Codex + Antigravity (prefixo `ai-` evita colisao)
- `dist/bin/ai.py` - copia **byte-a-byte** de `core/src/ai.py`
- `dist/bin/ai.ps1` - `core/bin/ai.ps1` com **substituicao literal** `..\src\ai.py` -> `ai.py`
- `dist/bin/ai` - shim POSIX bash (string literal no proprio renderer)
- `dist/templates/.githooks/commit-msg` + `features/registry.yaml` + `features/lock-ignore.txt` - copias byte-a-byte

**O que le:**
- `core/manifest/manifest.yaml` (skills)
- `core/src/ai.py` (engine) -> vira `dist/bin/ai.py`
- `core/bin/ai.ps1` (wrapper) -> adaptado pra `dist/bin/ai.ps1`
- 3 templates em `core/templates/` (lista estatica)

**CLI:**
- Sem args: gera tudo
- `--check`: exit 1 se algum target stale (compara saida renderizada com disco)
- `--verb <name>`: renderiza so um verbo, **pula bin/ e templates**

**Quem invoca:**
- `python core/build/render-skills.py` direto
- `.\core\bin\ai.ps1 render` (via `cmd_render` em `ai.py:398-408`)
- `python core/src/ai.py render`
- Documentacao CLAUDE.md exige rodar `--check` antes de entregar mudancas
- **Sem hook automatico no pre-commit** (o hook `commit-msg` so valida locks)

### Mapa do arquivo (262 linhas)

| Linhas | Bloco | Responsabilidade |
|---|---|---|
| 1-50 | docstring + imports + yaml com fallback | doc completa do que gera + import defensivo |
| 52-84 | constants | ROOT/paths/`TEMPLATE_FILES`/`TARGET_LABELS`/`POSIX_SHIM` literal |
| 87-91 | `load_manifest()` | `yaml.safe_load` do manifest |
| 94-101 | `agent_skill_name(verb)` | aplica prefixo `ai-` exceto se ja comeca com `ai-` |
| 104-109 | `target_path(target, verb)` | mapeia tipo de target -> path de saida |
| 112-130 | `render_skill_md` + `render_target` | wrapper de frontmatter YAML + corpo MD |
| 133-146 | `collect_outputs` | itera verbos+targets, lista de (path, target, verb, content) |
| 149-161 | `_adapt_wrapper_for_plugin` | substituicao literal `..\src\ai.py` -> `ai.py` |
| 164-178 | `collect_bin_outputs` | retorna 3 bin files (engine, wrapper adaptado, shim POSIX) |
| 181-196 | `collect_template_outputs` | copia templates listados em `TEMPLATE_FILES` |
| 199-221 | `write_outputs` + `check_outputs` | write se difere; check retorna stale list |
| 224-257 | `main()` | argparse + orquestracao |

### Perguntas estruturais

#### Q1 - Renderer esta pronto pra suportar layout B (Etapa 1.Q2)?

A migracao do manifest para "index + bodies markdown" depende **diretamente** deste renderer. Hoje [`render-skills.py:53`](../../core/build/render-skills.py) tem hardcoded `MANIFEST = ROOT / "core" / "manifest" / "manifest.yaml"`. E `collect_outputs` espera dict com `manifest["verbs"][verbo]["targets"][target]["body"]` literal string.

Para layout B precisaria:
- `load_manifest()` resolve referencias a arquivos externos (`body_file: "bodies/feature.claude.md"`)
- `collect_outputs` faz read do arquivo referenciado em vez de pegar string direto
- Provavelmente suporte a `shared_body` (Etapa 1.5)

**Recomendacao:** quando abrir a F-NNN do Etapa 1.Q2, **incluir refactor deste renderer no escopo**. Nao da pra separar - uma muda, a outra tambem.

#### Q2 - `TEMPLATE_FILES` hardcoded: auto-descobrir?

[Linhas 66-70](../../core/build/render-skills.py): lista estatica. Se alguem adicionar `core/templates/features/novo.txt`, ele **nao aparece em `dist/templates/`**.

Alternativas: A) Auto-discover via glob; B) Manter explicito + `--check` que detecta arquivos nao listados (fail loud); C) Mover para o manifest.

**Recomendacao:** B - consistencia com declarativo no manifest, fail loud.

#### Q3 - `dist/` nao e limpo entre runs: drift acumulado?

Se verbo for removido do manifest, `dist/skills/<old-verb>/SKILL.md` fica orfa. Renderer so escreve por cima. Hoje nao doeu porque o pack so cresceu. Mas quando o layout B chegar, restos da estrutura antiga ficam orfaos em `dist/`.

**Recomendacao:** `[FEATURE]` adicionar `--clean` (apaga `dist/` antes) ou `--check-orphans` (lista orfaos sem apagar).

#### Q4 - Validacao estrutural do manifest separada de comparacao com disco?

`--check` hoje faz dois jobs misturados: (1) renderiza em memoria, (2) compara com disco. Nao ha modo "so valida que o manifest e estruturalmente valido sem ler disco". Combina diretamente com **Etapa 1.7** (smoke tests).

**Recomendacao:** quando abrir F-NNN da Etapa 1.7, incluir aqui tambem. `--validate` separado: (a) schema manifest, (b) introspeccao CLI vs bodies, (c) confere marketplace.json.

### Achados (com path + linha)

| # | Onde esta (linha) | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | [`render-skills.py:53`](../../core/build/render-skills.py) `MANIFEST` literal | Acoplado a path unico. | (Em Q1, escopo conjunto com Etapa 1.Q2.) |
| 2 | [`render-skills.py:66-70`](../../core/build/render-skills.py) `TEMPLATE_FILES` hardcoded | Templates novos viram orfaos silenciosos. | (Em Q2.) |
| 3 | [`render-skills.py:149-161`](../../core/build/render-skills.py) `_adapt_wrapper_for_plugin` | Substituicao literal de marker unico. Warning vai pra stderr mas **write segue**. | Abortar com `sys.exit(2)` se marker ausente. |
| 4 | Sem CI/hook automatico rodando `--check` | Quem commitar mudanca em `ai.py` sem rodar render deixa `dist/` stale. | Pre-commit hook ou CI rodando `--check`. |
| 5 | [`render-skills.py:54-58`](../../core/build/render-skills.py) `DIST_DIR` hardcoded | Sem `--output-dir`; impossivel gerar em outro lugar. | Flag opcional. |
| 6 | [`render-skills.py:157-160`](../../core/build/render-skills.py) warning sem abortar | Linha 192 aborta. Linha 157 so warns. Inconsistente. | Padronizar warning critico = abort. |
| 7 | [`render-skills.py:210`](../../core/build/render-skills.py) `newline="\n"` em ai.ps1 | Convencao .gitattributes e CRLF; renderer escreve LF; checkout re-normaliza. Dev local rodando `--check` pode ver diff fantasma. | Renderer respeita politica de EOL por tipo. |
| 8 | [`render-skills.py:164-178`](../../core/build/render-skills.py) bin outputs | Nao gera `dist/bin/ai.cmd` (combina com Etapa 3.Q3). | Se 3.Q3 aprovar, incluir. |
| 9 | [`render-skills.py:137-145`](../../core/build/render-skills.py) `collect_outputs` | `spec=None` -> AttributeError; `targets={}` silencia verbo; `body=""` gera SKILL.md invalido sem warning. | Schema validation. (Combina com Etapa 1.7.) |
| 10 | [`render-skills.py:232`](../../core/build/render-skills.py) `--verb` pula bin/templates | Trade-off nao documentado. `--check --verb feature` nao detecta drift de engine. | Comentario inline ou flag `--include-bin`. |
| 11 | [`render-skills.py:112-122`](../../core/build/render-skills.py) `render_skill_md` frontmatter rigido | So `name`+`description`. Nao expoe `allowed-tools`, `model` etc. | Dict opcional de frontmatter extras. |
| 12 | [`render-skills.py:113`](../../core/build/render-skills.py) `desc = description.strip()` | Description vazia gera frontmatter invalido sem warning. | Abort/warning. (Combina com Etapa 1.7.) |
| 13 | [`render-skills.py:109` + `:130`](../../core/build/render-skills.py) `raise ValueError` | Traceback sujo em vez de mensagem amigavel. | Catch em main. |
| 14 | [`render-skills.py:91`](../../core/build/render-skills.py) `yaml.safe_load(...) or {}` | Manifest vazio "passa" com sucesso (gera nada). | Warning explicito. |
| 15 | `dist/` nao e limpo | Verbo/template removido fica orfao. | (Em Q3.) |
| 16 | Sem hooks pre/pos render | Nao da rodar `prettier`, `claude plugin validate` automaticamente. | Extensao pipeline. |
| 17 | [`render-skills.py:199-220`](../../core/build/render-skills.py) tuplas `(Path, str, str, str)` | Semi-opaco. | Refactor dataclass `Output`. |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | (combina com 1.Q2) | Refactor renderer ao migrar para layout B. **Escopo conjunto.** | proposto (composto) | - |
| Q2 | `[FEATURE]` | `TEMPLATE_FILES` validavel: `--check` detecta arquivos nao listados. | proposto | - |
| Q3 | `[FEATURE]` | `--clean` ou `--check-orphans` em `render-skills.py`. | proposto | - |
| Q4 | (combina com 1.7) | `--validate` separado de `--check`. | proposto (composto) | - |
| 3 | `[ISSUE]` | `_adapt_wrapper_for_plugin` aborta se marker ausente. | proposto | - |
| 4 | `[FEATURE]` | Pre-commit hook ou CI rodando `render --check`. | proposto | - |
| 5 | `[BACKLOG]` | `--output-dir` configuravel. | proposto | - |
| 6 | `[ISSUE]` | Padronizar warning-vs-abort em `render-skills.py`. | proposto | - |
| 7 | `[ISSUE]` | Renderer respeita politica de EOL por tipo de arquivo. | proposto | - |
| 8 | (combina com 3.Q3) | Gerar `dist/bin/ai.cmd` se 3.Q3 aprovar. | proposto (composto) | - |
| 9 | (combina com 1.7) | Schema validation em `collect_outputs`. | proposto (composto) | - |
| 10 | `[BACKLOG]` | Documentar trade-off de `--verb` pular bin/templates. | proposto | - |
| 11 | `[BACKLOG]` | Suporte a frontmatter extras (allowed-tools, model). | proposto | - |
| 12 | (combina com 1.7) | Description vazia gera warning/abort. | proposto (composto) | - |
| 13 | `[BACKLOG]` | Catch em `main()` para erros amigaveis. | proposto | - |
| 14 | `[BACKLOG]` | Warning quando manifest esta vazio. | proposto | - |
| 16 | `[BACKLOG]` | Hooks pre/pos render. | proposto | - |
| 17 | `[BACKLOG]` | Refactor tuplas -> dataclass `Output`. | proposto | - |

---

## Etapa 5 - `core/lock/check-lock.py`

### Proposito

**CLI standalone que valida e gerencia travas de edicao declaradas em `features/registry.yaml`.** E o portao que impede modificacoes acidentais a arquivos protegidos, exigindo `[unlock:<id>] motivo: <razao>` na mensagem do commit para liberar.

**O que esse arquivo faz:**
- Le `features/registry.yaml` (locks declarados) e `features/lock-ignore.txt` (paths que nunca podem ser travados)
- Bloqueia operacoes de git (add/modify/delete/rename) em arquivos travados
- Aceita liberacao temporaria via marker `[unlock:<id>]` no commit message
- 7 subcomandos: `list`, `check`, `lock`, `unlock`, `audit`, `hook`, `ci`
- Suporta lock por operacao especifica (`operations: [add]`) - "travar criacao mas liberar modificacao"
- Suporta glob patterns em `files:` (via `fnmatchcase`)
- Normaliza paths (`_norm`) - backslash -> slash
- Respeita `lock-ignore.txt`

**Quem invoca:**
- [`core/hooks/commit-msg`](../../core/hooks/commit-msg) - git hook (modo `hook`)
- CI pipelines (modo `ci`)
- Dev manualmente
- **`lock_task_files` em [`ai.py:626-658`](../../core/src/ai.py) NAO chama este script** - duplica logica (Etapa 2.Q3)

**De que depende:**
- `PyYAML` (obrigatorio, `sys.exit(2)` no import fail)
- `git` no PATH (so para `cmd_audit`)
- stdlib

### Mapa do arquivo (372 linhas)

| Linhas | Bloco | Responsabilidade |
|---|---|---|
| 1-50 | docstring + imports + yaml fallback | doc + import defensivo |
| 39-50 | constants | `REGISTRY`, `LOCK_IGNORE`, `UNLOCK_RE`, `ALL_OPERATIONS`, `REGISTRY_HEADER` |
| 53-101 | I/O helpers | `_norm`, `_matches_pattern`, `_load_lock_ignore`, `_is_ignored_path`, `_load_data`, `_load_locks`, `_save_locks` |
| 104-131 | matching | `_lock_operations`, `_lock_matches`, `_blocked`, `_filter_unlocked` |
| 134-153 | print formatting | `_print_block` |
| 155-184 | event inference | `_infer_operation`, `_events_from_paths`, `_events_from_name_status` |
| 189-328 | subcomandos | `cmd_list`, `cmd_check`, `cmd_lock`, `cmd_unlock`, `cmd_audit`, `cmd_hook`, `cmd_ci` |
| 333-372 | argparse + main | entry point |

### Perguntas estruturais

#### Q1 - Duplicacao com `lock_task_files` (Etapa 2.Q3): prioridade?

Ja capturado em **Etapa 2.Q3**. Reforco aqui porque a duplicacao tem **efeito real**:
- `lock_task_files` **nao respeita `lock-ignore.txt`** - pode travar `.gitignore`
- Nao normaliza paths via `_norm()` -> Windows backslash vira mismatch
- Sempre bloqueia 4 operacoes; ignora `operations: [add]`

**Recomendacao:** quando abrir F-NNN de Etapa 2.Q3, **incluir refactor que exporte modulo `check_lock_api`** reutilizavel por `ai.py`. Nao e so "DRY" - e correcao de bug latente.

#### Q2 - CLI gestao de locks tem buracos: `info`, `edit`, `history`?

| Quero fazer... | Hoje | Problema |
|---|---|---|
| Ver detalhes de **um** lock | `list` + filtrar | Sem `info <id>` |
| Adicionar arquivo a lock **existente** | `unlock` + `lock` | **Perde historico** |
| Ver quando lock foi criado/modificado | `audit` (so unlocks via git log) | Sem historico estruturado |
| Renomear lock id | manual YAML + commit | Sem subcomando |

**Recomendacao:** `[FEATURE]` 3 subcomandos: `info <id>`, `edit <id> --add-file ...`, `history <id>`. Combina com Q3.

#### Q3 - Output nao-estruturado para CI

Todas saidas sao prosa PT-BR. CI precisa parsear texto.

**Recomendacao:** `[FEATURE]` flag `--json` em `list`, `check`, `audit`, `info`. Combina com tendencia geral (Etapa 1.10, Etapa 2.11).

#### Q4 - Wildcard `*` em `cmd_lock` bypassa `lock-ignore.txt`: design ou pegadinha?

[Linha 219-220](../../core/lock/check-lock.py) - `*` escapa a checagem. Template default usa `files: ['*']` operacao `[add]` - trava criacao de qualquer arquivo **inclusive `.gitignore`**.

**Decisao a tomar:** intencional (lock blanket "adicoes-exigem-autorizacao" precisa cobrir tudo) ou bug (lock-ignore deveria sempre vencer)?

**Recomendacao:** **intencional + comentario inline**. Se for bug, mudar para `_is_ignored_path` respeitado mesmo em wildcards, e lock blanket usar `files: ['**/*']` com excecoes.

### Achados (com path + linha)

| # | Onde esta (linha) | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | (capturado em 2.Q3) | Duplicacao com `ai.py:lock_task_files`. | (Em 2.Q3 - reforco aqui.) |
| 2 | [`check-lock.py:75-76`](../../core/lock/check-lock.py) `_is_ignored_path` chama `_load_lock_ignore` toda invocacao | Re-le o arquivo a cada path. Hook commit-msg com 50 staged files = 50 reads. | `@functools.cache` em `_load_lock_ignore`. |
| 3 | [`check-lock.py:249-272`](../../core/lock/check-lock.py) `cmd_audit` | Falha silenciosa fora de repo git ("Erro ao consultar git log"). | Detectar `git rev-parse` primeiro; mensagem clara. |
| 4 | (em Q2) | Sem `info <id>`. | Novo subcomando. |
| 5 | (em Q2) | Sem `edit <id>` - adicionar arquivo perde historico. | Novo subcomando. |
| 6 | (em Q2) | Sem `history <id>` - nao sabe quem criou/modificou. | Novo subcomando + log no registry. |
| 7 | [`check-lock.py:43`](../../core/lock/check-lock.py) `ALL_OPERATIONS = ("add", "modify", "delete", "rename")` | Nao cobre `chmod`, `copy`. | Comentario inline OU listar `not-supported`. |
| 8 | [`check-lock.py:93-101`](../../core/lock/check-lock.py) `_save_locks` reescreve registry inteiro | Concorrencia: 2 locks simultaneos = last-write-wins. | Comentario inline. |
| 9 | [`check-lock.py:219-220`](../../core/lock/check-lock.py) wildcard `*` bypassa `_is_ignored_path` | (Em Q4.) | (Em Q4.) |
| 10 | [`check-lock.py:223-224`](../../core/lock/check-lock.py) `cmd_lock` avisa arquivo inexistente mas continua | Bom para "trava futuro", ruim para typo. | Flag `--allow-missing`; sem flag, abortar. |
| 11 | [`check-lock.py:238-246`](../../core/lock/check-lock.py) `cmd_unlock` permanente sem confirmacao | Sem soft delete, sem audit local. | Confirmacao interativa OU `--force`; combina com Q2. |
| 12 | [`check-lock.py:303-328`](../../core/lock/check-lock.py) `cmd_ci` recebe paths de 2 arquivos | CI-friendly mas estranho. | Doc clara OU suporte stdin. |
| 13 | Todas saidas em prosa PT | (Em Q3.) | (Em Q3.) |
| 14 | [`check-lock.py:42`](../../core/lock/check-lock.py) `UNLOCK_RE` | Nao exige `motivo:` no mesmo commit. | Padrao estendido OU validacao adicional. |
| 15 | [`check-lock.py:205-211`](../../core/lock/check-lock.py) `cmd_check` retorna 1 quando acha lock | Pra dev "quero ver se esta travado", confunde. | Doc clara. |
| 16 | Sem `--dry-run` em `cmd_lock` | Util para preview. | Flag opcional. |
| 17 | strings PT-BR | (Combina com Etapa 1.4.) | (Em 1.4.) |
| 18 | Sem teste automatizado | (Combina com Etapa 2.15.) | (Em 2.15.) |
| 19 | [`check-lock.py:55`](../../core/lock/check-lock.py) `_norm` nao previne path traversal | Dev poderia travar arquivo fora do repo via CLI manual. | `Path.resolve()` + `is_relative_to(REPO_ROOT)`. |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | (composto com 2.Q3) | Extrair modulo importavel; corrigir bug latente em `lock_task_files`. | proposto (composto) | - |
| Q2 | `[FEATURE]` | Subcomandos `info <id>`, `edit <id>`, `history <id>`. | proposto | - |
| Q3 | `[FEATURE]` | Flag `--json` em `list`, `check`, `audit`, `info`. | proposto | - |
| Q4 | `[ISSUE]` ou `[BACKLOG]` | Decisao: wildcard `*` deve respeitar `lock-ignore.txt`? | proposto | - |
| 2 | `[BACKLOG]` | Cache em `_load_lock_ignore` (perf de hook). | proposto | - |
| 3 | `[ISSUE]` | `cmd_audit` mensagem clara fora de repo git. | proposto | - |
| 7 | `[BACKLOG]` | Doc das `ALL_OPERATIONS` e operacoes nao suportadas. | proposto | - |
| 8 | `[BACKLOG]` | Comentario inline sobre concorrencia em `_save_locks`. | proposto | - |
| 10 | `[ISSUE]` | `cmd_lock` aborta em arquivo inexistente sem `--allow-missing`. | proposto | - |
| 11 | `[BACKLOG]` | `cmd_unlock` exige confirmacao ou `--force`. | proposto | - |
| 12 | `[BACKLOG]` | `cmd_ci` aceita stdin. | proposto | - |
| 14 | `[ISSUE]` | `UNLOCK_RE` valida que `motivo:` esta no mesmo commit. | proposto | - |
| 15 | `[BACKLOG]` | Mensagem clara em `cmd_check` sobre exit 1. | proposto | - |
| 16 | `[BACKLOG]` | `--dry-run` em `cmd_lock`. | proposto | - |
| 19 | `[ISSUE]` | `_norm` previne path traversal (seguranca). | proposto | - |

---

## Etapa 6 - hooks (`core/hooks/commit-msg` + `core/templates/.githooks/commit-msg`)

### Proposito

**Git hook shim que delega a validacao de locks ao `check-lock.py hook`.** Roda automaticamente antes do git aceitar o commit, recebendo o path da mensagem como argumento. Se o `check-lock.py` retornar nao-zero, o commit e cancelado.

**Por que existem DOIS arquivos (confirmado byte-a-byte identicos):**

| Arquivo | Funcao | Quando vira hook ativo |
|---|---|---|
| [`core/hooks/commit-msg`](../../core/hooks/commit-msg) | Hook **ativo no repo-mae** | Dev roda `git config core.hooksPath core/hooks` uma vez por clone |
| [`core/templates/.githooks/commit-msg`](../../core/templates/.githooks/commit-msg) | **Template** copiado para `dist/templates/.githooks/commit-msg` pelo renderer | Instalador (B-008, ainda inexistente) deposita no consumidor |

**O que o hook faz (mesmo nos dois):**
1. Resolve `$ROOT` = top-level do repo via `git rev-parse --show-toplevel`
2. Procura Python no PATH com fallback `python3 -> python -> py`
3. Filtra stub do Microsoft Store (Windows) testando se `--version` realmente retorna
4. Aborta com exit 2 se nao acha Python
5. Faz `exec "$PY" "$ROOT/core/lock/check-lock.py" hook "$1"` - substitui processo, propaga exit code

**Dependencias:**
- POSIX sh (`#!/bin/sh`)
- `git` (para `rev-parse`)
- Python 3 no PATH
- `core/lock/check-lock.py` existir relativo ao ROOT do git

**Quem invoca:**
- git automaticamente em `git commit`, antes de aceitar a mensagem

### Perguntas estruturais

#### Q1 - Duplicacao byte-a-byte: fonte unica + copia via renderer?

**Confirmado identico** (via `diff -u`). Padrao exato do que ja existe pra `core/src/ai.py` -> `dist/bin/ai.py` (renderer copia byte-a-byte).

**Plano sugerido:**
- Manter [`core/hooks/commit-msg`](../../core/hooks/commit-msg) como **fonte unica** (e o que esta ativo no repo-mae)
- Adicionar entrada em `TEMPLATE_FILES` ([`render-skills.py:66-70`](../../core/build/render-skills.py)) mapeando `core/hooks/commit-msg` -> `dist/templates/.githooks/commit-msg`
- **Apagar `core/templates/.githooks/commit-msg`**

**Risco:** zero. O arquivo de template e so usado pelo renderer; nada na cadeia atual aponta direto pra ele.

**Recomendacao:** `[ISSUE]` - fix simples, alto valor.

#### Q2 - Template nao funciona out-of-the-box no consumidor (path hardcoded)?

[Linha 23 do hook](../../core/hooks/commit-msg):
```sh
exec "$PY" "$ROOT/core/lock/check-lock.py" hook "$1"
```

Assume que `check-lock.py` mora em `$ROOT/core/lock/`. **Funciona no repo-mae** (path coincide). **Nao funciona no consumidor** se o instalador depositar o pack em outro lugar.

**Duas saidas possiveis:**
- **A) Hook parametrizado:** template tem `__PACK_ROOT__/core/lock/check-lock.py`, instalador substitui no momento de deploy.
- **B) Convencao fixa:** documentar que o pack **deve** ser instalado em `<consumer>/core/` (sem prefixo).

**Recomendacao:** `[BACKLOG]` - so vira problema quando o instalador for entregue (B-008). Mas vale **registrar agora**.

#### Q3 - `py` no candidate list de hook POSIX?

[Linha 12](../../core/hooks/commit-msg): `for cmd in python3 python py; do`. `py` e o **Windows Python launcher**. Em Linux/Mac, `command -v py` retorna vazio, loop pula. Nao causa erro mas:
- Confunde leitor
- Adiciona overhead trivial

**Recomendacao:** `[BACKLOG]` - remover `py` do hook POSIX. Cleanup minimo.

### Achados (com linha)

| # | Onde esta | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | Os dois arquivos | **Duplicacao byte-a-byte confirmada.** | (Em Q1.) |
| 2 | Linha 23 ambos | Path `core/lock/check-lock.py` hardcoded; quebra no consumidor sem instalador. | (Em Q2.) |
| 3 | Linha 12 ambos | `py` em script POSIX. | (Em Q3.) |
| 4 | Nenhum dos arquivos | Sem tag de versao. Se contrato mudar, consumidor nao sabe atualizar. | Comentario `# version: X` no header + check opcional. |
| 5 | Linha 13 ambos: `"$cmd" --version >/dev/null 2>&1` | Aceita qualquer versao Python (mesmo 2.7 se estivesse no PATH). | (Combina com Etapa 3.5.) |
| 6 | Linha 20: `echo "Erro: Python nao encontrado..."` | Mensagem so em PT. | (Combina com Etapa 1.4.) |
| 7 | Sem `set -eu` | Variaveis indefinidas viram string vazia silenciosa. | `set -eu` no topo. |
| 8 | Instalacao manual de `git config core.hooksPath core/hooks` | Sem deteccao/aviso se consumidor ja tem `core.hooksPath` setado. | Doc + script install/uninstall (combina com B-008). |
| 9 | Mensagem de erro de Python ausente lista paths tentados | (Combina com Etapa 3.4.) | (Em 3.4.) |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | `[ISSUE]` | Deduplicar: fonte unica em `core/hooks/commit-msg`, renderer copia para `dist/templates/.githooks/`. | proposto | - |
| Q2 | `[BACKLOG]` | Hook parametrizado para consumidor (path do pack via placeholder). **Combina com B-008.** | proposto | - |
| Q3 | `[BACKLOG]` | Remover `py` do candidate list em hook POSIX. | proposto | - |
| 4 | `[BACKLOG]` | Tag de versao no header do hook + check opcional. | proposto | - |
| 5 | (composto com 3.5) | Validacao de versao Python no hook. | proposto (composto) | - |
| 6 | (composto com 1.4) | Mensagem de erro em PT/EN. | proposto (composto) | - |
| 7 | `[BACKLOG]` | `set -eu` no topo do hook. | proposto | - |
| 8 | (composto com B-008) | Deteccao de `core.hooksPath` existente; script install/uninstall. | proposto (composto) | - |
| 9 | (composto com 3.4) | Mensagem de erro lista paths tentados. | proposto (composto) | - |

---

## Etapa 7 - `core/templates/features/*`

### Proposito

**Templates que servem como estado inicial depositado pelo instalador no consumidor.** Quando o pack for instalado em outro projeto (via B-008, ainda inexistente), estes arquivos viram o ponto de partida em `<consumer>/features/`. No proprio repo-mae, eles foram a base do `features/registry.yaml` e `features/lock-ignore.txt` ativos.

**Os dois arquivos:**

[`core/templates/features/registry.yaml`](../../core/templates/features/registry.yaml) (12 linhas) - traz lock default `adicoes-exigem-autorizacao` com `files: ['*']` operacao `[add]`.

[`core/templates/features/lock-ignore.txt`](../../core/templates/features/lock-ignore.txt) (5 linhas) - so lista `.gitignore` e ele mesmo.

**Quem consome:**
- `render-skills.py` copia byte-a-byte para `dist/templates/features/`
- Instalador futuro (B-008) deposita no consumer
- `core/lock/check-lock.py` le os arquivos **resolvidos** (nao os templates) em `features/registry.yaml` e `features/lock-ignore.txt`

**De que dependem:**
- Schema definido implicitamente por `check-lock.py` (sem JSON Schema formal)
- Comentarios referenciam `docs/reference/registry-yaml.md` e `docs/explanation/por-que-lock.md`

### Perguntas estruturais

#### Q1 - Lock default `adicoes-exigem-autorizacao` e onboarding aspero?

Template default ja vem com trava ativa: **qualquer arquivo novo precisa de `[unlock:adicoes-exigem-autorizacao]` no commit**. Implica:
- Primeiro commit do consumer com arquivo novo encontra friccao
- Onboarding aspero
- Combina com Etapa 5.Q4 (wildcard `*` bypassa `lock-ignore.txt`)

**3 opcoes:** A (atual, lock ativo); B (opt-in via flag); C (opt-out, lock + doc).

**Recomendacao:** decisao do dev. Se pack mira "disciplina forte", A + melhor doc. Se mira "adocao facil", B.

#### Q2 - Faltam templates para outros artefatos do pack?

| Arquivo | Existe? | Importancia |
|---|---|---|
| `.ai/process.json` | Nao | Alta - schema do processo |
| `.ai/docs-map.yaml` | Nao | Alta - ativa docs-hook |
| `.ai/backlog.json`, `.ai/tasks.json` | Nao | Media - estado |
| `CLAUDE.md` | Nao | **Critica** - instrucoes pra IA |
| `AGENTS.md` | Nao | **Critica** - idem |
| `features/README.md` | Nao | Media - protocolo lock |

Consumer recem-instalado **so tem 2 dos ~7 arquivos necessarios** com ponto de partida claro.

**Recomendacao:** `[FEATURE]` adicionar templates faltantes. **Combina com B-008** (instalador materializa).

#### Q3 - `lock-ignore.txt` enxuto: ampliar default ou deixar minimo?

Hoje so protege `.gitignore` e ele mesmo. Candidatos obvios: `CHANGELOG.md`, `README.md`, `package.json` / `pyproject.toml`, `docs/**`.

**Tensao:** minimo (pack neutro) vs ampliado (consumer protegido).

**Recomendacao:** `[BACKLOG]` decisao do dev.

### Achados (com linha)

| # | Onde esta | O que esta errado | Onde corrigir |
|---|---|---|---|
| 1 | [`registry.yaml:6-11`](../../core/templates/features/registry.yaml) lock default | Onboarding aspero. | (Em Q1.) |
| 2 | Pack inteiro | Faltam templates para `process.json`, `docs-map.yaml`, `CLAUDE.md`, `AGENTS.md`, `features/README.md`. | (Em Q2.) |
| 3 | [`lock-ignore.txt`](../../core/templates/features/lock-ignore.txt) | Lista enxuta. | (Em Q3.) |
| 4 | [`registry.yaml:5`](../../core/templates/features/registry.yaml) `version: 1` | Sem migracao de schema futura prevista. | Doc no `docs/reference/registry-yaml.md`. |
| 5 | [`registry.yaml:1-3`](../../core/templates/features/registry.yaml) comentarios PT | (Combina com Etapa 1.4.) | (Em 1.4.) |
| 6 | [`lock-ignore.txt:1-2`](../../core/templates/features/lock-ignore.txt) comentarios EN | Inconsistencia: registry PT, lock-ignore EN. | (Em 1.4.) |
| 7 | Renderer nao valida que templates sao YAML/TXT validos | Copia byte-a-byte; corrupcao so pega no consumer. | Renderer faz `yaml.safe_load` em `.yaml` antes de copiar. |
| 8 | Templates hardcoded em `core/templates/features/` | Layout consumer assumido. | (Combina com 6.Q2.) |
| 9 | Mistura `.yaml` vs `.txt` para configs adjacentes | Razoavel mas vale comentario inline. | Comentario em `lock-ignore.txt`. |

### Candidatos

| # | Classificacao proposta | Resumo | STATUS | ID final |
|---|---|---|---|---|
| Q1 | `[BACKLOG]` | Decidir destino do lock default (A/B/C). | proposto | - |
| Q2 | `[FEATURE]` | Templates faltantes: process.json, docs-map.yaml, CLAUDE.md, AGENTS.md, features/README.md. **Combina com B-008.** | proposto (composto) | - |
| Q3 | `[BACKLOG]` | Decidir destino do `lock-ignore.txt`: minimo ou ampliado. | proposto | - |
| 4 | `[BACKLOG]` | Doc sobre migracao de schema do `registry.yaml`. | proposto | - |
| 5 | (composto com 1.4) | Padronizar idioma de comentarios do template. | proposto (composto) | - |
| 6 | (composto com 1.4) | Resolver inconsistencia PT/EN entre os dois templates. | proposto (composto) | - |
| 7 | `[ISSUE]` | Renderer valida YAML antes de copiar (`yaml.safe_load`). | proposto | - |
| 8 | (composto com 6.Q2) | Parametrizacao de path no template. | proposto (composto) | - |
| 9 | `[BACKLOG]` | Comentario inline em `lock-ignore.txt` explicando escolha de formato. | proposto | - |

---

## Clusters de disparo (agrupamento recomendado)

Vários candidatos sao **compostos** - olham o mesmo escopo de angulos diferentes. **Nao abrir como F-/I-/B- separadas** - virar 1 F unica com escopo combinado. Cada cluster abaixo lista os itens que deveriam entrar juntos.

| Cluster | Itens | Sugestao de titulo |
|---|---|---|
| **Layout B do manifest** | 1.Q2 (ja aprovada) + 1.5 + 4.Q1 | "Migrar manifest para layout B (index + bodies markdown + shared_body)" |
| **Smoke tests / validacao manifest** | 1.7 + 4.Q4 + 4.9 + 4.12 | "Smoke tests + schema validation no render --check" |
| **Lock module compartilhado** | 2.Q3 + 5.Q1 | "Extrair lock logic em modulo importavel; ai.py consome" |
| **`.cmd` shim** | 3.Q3 + 4.8 | "Criar core/bin/ai.cmd + gerar dist/bin/ai.cmd via renderer" |
| **Politica PT/EN** | 1.4 + 6.6 + 7.5 + 7.6 | "Definir e aplicar politica PT/EN em bodies/templates/hooks" |
| **Validacao versao Python** | 3.5 + 6.5 | "Validar versao Python (>= 3.10) em wrappers e hook" |
| **Mensagem de erro Python ausente** | 3.4 + 6.9 | "Mensagem com paths tentados e sugestao de instalacao" |
| **B-008 (instalador)** | 6.Q2 + 7.Q2 + 7.8 + 6.8 | (combina com backlog ja existente de outro escopo) |

### Recomendacao de ordem (se priorizar por destravar outros)

1. **Layout B do manifest** primeiro - destrava varios outros (afeta renderer, schema, shared_body, validacao).
2. **Lock module compartilhado** - corrige bug latente em `lock_task_files` (pode travar `.gitignore`).
3. **Smoke tests** - depois de Layout B, pra validar o novo schema.
4. **Demais clusters** - ordem livre, baixo acoplamento entre si.

## Consolidado (fonte de verdade pro disparo em lote)

Tabela mestre de TODOS os candidatos das 7 etapas. Atualizada conforme o dev avalia e os IDs sao atribuidos pelo CLI no fim.

| Origem (etapa.#) | Classificacao | STATUS | ID | Titulo curto |
|---|---|---|---|---|
| 1.Q1 | `[BACKLOG]` | proposto | - | ADR 0007 documentando escolha de YAML pra manifest |
| **1.Q2** | **`[FEATURE]`** | **aprovado** | - | **Migrar manifest pra layout B (index YAML + bodies markdown)** |
| 1.Q3 | (capturado em 1.7) | - | - | (consolidado no achado 7) |
| 1.1 | `[ISSUE]` | proposto | - | Alinhar bodies claude_skill com flags reais do CLI |
| 1.2 | `[FEATURE]` | proposto | - | Shims faltando: doctor, render, docs-check, lock, unlock, audit |
| 1.3 | `[ISSUE]` | proposto | - | Rodape "Then continue using ai-process" em promote/finish |
| 1.4 | `[BACKLOG]` | proposto | - | Politica PT vs EN para skill bodies |
| 1.5 | `[BACKLOG]` | proposto | - | shared_body + overrides no manifest (combina com Q2) |
| 1.6 | `[BACKLOG]` | proposto | - | Documentar prefixos PRIMARY TRIGGER/DEFER-AND-PARK em ADR |
| 1.7 | `[FEATURE]` | proposto | - | Smoke tests do manifest no `render-skills.py --check` |
| 1.8 | `[ISSUE]` | proposto | - | Body do promote deve dizer que cria branch `codex/<slug>` |
| 1.9 | `[BACKLOG]` | proposto | - | Fallback `python core/src/ai.py` em cada skill body |
| 1.10 | `[NO-OP]` | proposto | - | backlog list sem ordem/paginacao - esperar crescer |
| 1.11 | `[ISSUE]` | proposto | - | $ARGUMENTS em PS com argumentos contendo aspas |
| 2.Q1 | `[FEATURE]`/`[BACKLOG]` | proposto | - | Split de `core/src/ai.py` em modulos por responsabilidade |
| 2.Q2 | `[ISSUE]` | proposto | - | `validate` com warning explicito; remocao em N+2 |
| 2.Q3 | `[FEATURE]` | proposto | - | Extrair lock logic de check-lock.py em modulo importavel |
| 2.Q4 | `[ISSUE]` | proposto | - | `finish` pre-valida locks antes de commit |
| 2.1 | `[ISSUE]` | proposto | - | Remover `cleanup_task_worktree` duplicado em `cmd_finish` |
| 2.2 | `[ISSUE]` | proposto | - | `cmd_promote` deve gravar backlog so apos task confirmada |
| 2.4 | `[ISSUE]` | proposto | - | Normalizar paths em `commit_task` (Windows backslash) |
| 2.5 | `[BACKLOG]` | proposto | - | Erro de `find_task_or_current` lista IDs recentes |
| 2.6 | `[BACKLOG]` | proposto | - | `upsert_features_entry` configuravel |
| 2.7 | `[BACKLOG]` | proposto | - | Remover hardcoded `FEATURES.md` em `new_task` |
| 2.8 | `[BACKLOG]` | proposto | - | ADR/doc "convention over config" pros paths fixos |
| 2.9 | `[ISSUE]` | proposto | - | `cmd_finish --no-commit` nao remove worktree |
| 2.10 | `[FEATURE]` | proposto | - | Estender `cmd_doctor` (manifest/PyYAML/git/render/dist) |
| 2.11 | `[FEATURE]` | proposto | - | Subcomandos `tasks list/show/filter` |
| 2.12 | `[ISSUE]` | proposto | - | Mensagem clara quando git nao esta no PATH |
| 2.13 | `[ISSUE]` | proposto | - | `attach_worktree` pre-checa existencia de branch |
| 2.15 | `[FEATURE]` | proposto | - | Pytest com smoke tests dos subcomandos |
| 3.Q1 | `[FEATURE]` | proposto | - | Criar `core/bin/ai` (shim POSIX bash) simetrico ao `dist/bin/ai` |
| 3.Q2 | `[FEATURE]` | proposto | - | Refactor `Resolve-Python` com estrategia em camadas |
| 3.Q3 | `[BACKLOG]` | proposto | - | `core/bin/ai.cmd` para cmd.exe |
| 3.4 | `[ISSUE]` | proposto | - | Mensagem de erro Python ausente: paths tentados + sugestao instalar |
| 3.5 | `[ISSUE]` | proposto | - | `Test-Python` valida versao >= 3.10 |
| 3.6 | `[BACKLOG]` | proposto | - | Renomear param `$Args` -> `$Arguments` |
| 3.7 | `[BACKLOG]` | proposto | - | Flag `-Verbose` mostra Python selecionado |
| 3.8 | `[ISSUE]` | proposto | - | Pre-checar existencia de `core/src/ai.py` |
| 3.11 | `[BACKLOG]` | proposto | - | Centralizar logica especial de `py` em funcao unica |
| 3.12 | `[BACKLOG]` | proposto | - | Comentario inline explicando `$ErrorActionPreference = "Stop"` |
| 4.Q1 | (composto com 1.Q2) | proposto | - | Refactor renderer ao migrar para layout B (escopo conjunto) |
| 4.Q2 | `[FEATURE]` | proposto | - | `TEMPLATE_FILES` validavel: `--check` detecta arquivos nao listados |
| 4.Q3 | `[FEATURE]` | proposto | - | `--clean` ou `--check-orphans` em `render-skills.py` |
| 4.Q4 | (composto com 1.7) | proposto | - | `--validate` separado de `--check` |
| 4.3 | `[ISSUE]` | proposto | - | `_adapt_wrapper_for_plugin` aborta se marker ausente |
| 4.4 | `[FEATURE]` | proposto | - | Pre-commit hook ou CI rodando `render --check` |
| 4.5 | `[BACKLOG]` | proposto | - | `--output-dir` configuravel |
| 4.6 | `[ISSUE]` | proposto | - | Padronizar warning-vs-abort em `render-skills.py` |
| 4.7 | `[ISSUE]` | proposto | - | Renderer respeita politica de EOL por tipo de arquivo |
| 4.8 | (composto com 3.Q3) | proposto | - | Gerar `dist/bin/ai.cmd` se 3.Q3 aprovar |
| 4.9 | (composto com 1.7) | proposto | - | Schema validation em `collect_outputs` |
| 4.10 | `[BACKLOG]` | proposto | - | Documentar trade-off de `--verb` pular bin/templates |
| 4.11 | `[BACKLOG]` | proposto | - | Suporte a frontmatter extras (allowed-tools, model) |
| 4.12 | (composto com 1.7) | proposto | - | Description vazia gera warning/abort |
| 4.13 | `[BACKLOG]` | proposto | - | Catch em `main()` para erros amigaveis |
| 4.14 | `[BACKLOG]` | proposto | - | Warning quando manifest esta vazio |
| 4.16 | `[BACKLOG]` | proposto | - | Hooks pre/pos render |
| 4.17 | `[BACKLOG]` | proposto | - | Refactor tuplas -> dataclass `Output` |
| 5.Q1 | (composto com 2.Q3) | proposto | - | Extrair modulo importavel; corrigir bug latente em `lock_task_files` |
| 5.Q2 | `[FEATURE]` | proposto | - | Subcomandos `info <id>`, `edit <id>`, `history <id>` em check-lock |
| 5.Q3 | `[FEATURE]` | proposto | - | Flag `--json` em check-lock (list/check/audit/info) |
| 5.Q4 | `[ISSUE]`/`[BACKLOG]` | proposto | - | Wildcard `*` em cmd_lock: respeitar lock-ignore ou documentar |
| 5.2 | `[BACKLOG]` | proposto | - | Cache em `_load_lock_ignore` (perf de hook) |
| 5.3 | `[ISSUE]` | proposto | - | `cmd_audit` mensagem clara fora de repo git |
| 5.7 | `[BACKLOG]` | proposto | - | Doc das `ALL_OPERATIONS` e operacoes nao suportadas |
| 5.8 | `[BACKLOG]` | proposto | - | Comentario inline sobre concorrencia em `_save_locks` |
| 5.10 | `[ISSUE]` | proposto | - | `cmd_lock` aborta em arquivo inexistente sem `--allow-missing` |
| 5.11 | `[BACKLOG]` | proposto | - | `cmd_unlock` exige confirmacao ou `--force` |
| 5.12 | `[BACKLOG]` | proposto | - | `cmd_ci` aceita stdin |
| 5.14 | `[ISSUE]` | proposto | - | `UNLOCK_RE` valida `motivo:` no mesmo commit |
| 5.15 | `[BACKLOG]` | proposto | - | Mensagem clara em `cmd_check` sobre exit 1 |
| 5.16 | `[BACKLOG]` | proposto | - | `--dry-run` em `cmd_lock` |
| 5.19 | `[ISSUE]` | proposto | - | `_norm` previne path traversal (seguranca) |
| 6.Q1 | `[ISSUE]` | proposto | - | Deduplicar hooks (fonte unica + renderer copia para dist/templates) |
| 6.Q2 | `[BACKLOG]` | proposto | - | Hook parametrizado para consumidor (combina com B-008) |
| 6.Q3 | `[BACKLOG]` | proposto | - | Remover `py` do candidate list em hook POSIX |
| 6.4 | `[BACKLOG]` | proposto | - | Tag de versao no header do hook + check opcional |
| 6.5 | (composto com 3.5) | proposto | - | Validacao de versao Python no hook |
| 6.6 | (composto com 1.4) | proposto | - | Mensagem de erro do hook em PT/EN |
| 6.7 | `[BACKLOG]` | proposto | - | `set -eu` no topo do hook |
| 6.8 | (composto com B-008) | proposto | - | Deteccao de `core.hooksPath` existente; script install/uninstall |
| 6.9 | (composto com 3.4) | proposto | - | Mensagem de erro do hook lista paths tentados |
| 7.Q1 | `[BACKLOG]` | proposto | - | Decidir destino do lock default (A/B/C - manter, opt-in, opt-out) |
| 7.Q2 | `[FEATURE]` (composto com B-008) | proposto | - | Templates faltantes: process.json, docs-map.yaml, CLAUDE.md, AGENTS.md, features/README.md |
| 7.Q3 | `[BACKLOG]` | proposto | - | Decidir destino do `lock-ignore.txt`: minimo ou ampliado |
| 7.4 | `[BACKLOG]` | proposto | - | Doc sobre migracao de schema do `registry.yaml` |
| 7.5 | (composto com 1.4) | proposto | - | Padronizar idioma de comentarios do template |
| 7.6 | (composto com 1.4) | proposto | - | Inconsistencia PT/EN entre os dois templates |
| 7.7 | `[ISSUE]` | proposto | - | Renderer valida YAML antes de copiar |
| 7.8 | (composto com 6.Q2) | proposto | - | Parametrizacao de path no template |
| 7.9 | `[BACKLOG]` | proposto | - | Comentario inline em `lock-ignore.txt` explicando escolha de formato |
