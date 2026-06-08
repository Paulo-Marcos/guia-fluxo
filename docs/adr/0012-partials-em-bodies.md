# ADR-0012: Partials includes em bodies do manifest

- **Status:** Aceita
- **Data:** 2026-06-08

## Contexto

O Layout B (ADR-0008) resolveu a dor de bodies inline em YAML: cada body
virou markdown puro em `core/manifest/bodies/<verb>.<target>.md`. Diff e
preview ficaram limpos, e a navegacao do index melhorou.

O que **nao** foi resolvido por ele e que doeu na pratica em D-047:

1. **Duplicacao semantica entre hosts.** `feature.agent.md` e
   `feature.claude.md` tem ~70% do conteudo identico (sintese de titulo,
   linha de comando, ler `current-task.json`, repetir `NOME DO CHAT`).
   So divergem na linha de renomeacao de chat (Codex App
   `codex_app.set_thread_title` vs Claude `/rename` + alternativas).
2. **Duplicacao entre shims.** O "fluxo pos-CLI" (ler current-task,
   repetir nome, renomear chat) e literalmente o mesmo texto em 7 verbos
   (feature/bug/chore/backlog/promote/ready/finish). Editar a regra de
   renomeacao significava varrer 14 arquivos.
3. **Skill-mae sobrecarregada.** `guia-fluxo.{agent,claude}.md` carregava
   uma secao "Agent Behavior" com 13 itens — varios dos quais eram regras
   que cada shim ja deveria contar por si. O agente precisava "voltar pra
   mae" como hint textual ("Then continue using guia-fluxo"), o que
   funcionava no Claude (auto-load por description) mas era fragil no
   Codex/Antigravity.
4. **Promessa quebrada de rename no Claude.** O texto dos shims dizia
   "rode `/rename <suggested-title>` se Claude supports it" — em pratica
   so funciona em alguns builds. O usuario via "NOME DO CHAT" impresso
   mas o chat nao renomeava de fato; nao havia alternativa.

## Decisao

Introduzir uma diretiva `{{include: <path>}}` no
`core/build/render-skills.py`. Bodies podem incluir trechos
compartilhados de `core/manifest/bodies/_partials/`. A expansao ocorre em
build-time; o `SKILL.md` final em `dist/` continua self-contained
(nenhuma indirecao em runtime do agente).

Catalogo inicial em `_partials/`:

- `title_context_rules.md` (host-agnostic) — regras de sintese
  `<title>` vs `<context>`. Incluido pelos verbos de criacao
  (feature, bug, chore, backlog).
- `lock_protocol.md` (host-agnostic) — protocolo de unlock detalhado.
  Incluido por verbos que editam arquivos (feature, bug, chore,
  promote, finish).
- `post_cli.agent.md` — fluxo pos-CLI para Codex/Antigravity
  (`codex_app.list_threads` + `codex_app.set_thread_title`, ou fallback
  textual para Antigravity).
- `post_cli.claude.md` — fluxo pos-CLI para Claude Code, usando
  `mark_chapter` (`mcp__ccd_session__mark_chapter`) como **surrogate
  confiavel de rename** (divisor visivel + ToC entry), com `/rename` como
  bonus quando o build suporta.

Schema do renderer (extension de ADR-0008):

```python
# Em core/build/render-skills.py:
INCLUDE_RE = re.compile(r"^\{\{include:\s*([^}\s][^}]*?)\s*\}\}$", re.MULTILINE)

def _expand_includes(text, origin, body_cache, stack=()):
    # paths relativos ao **diretorio do arquivo que inclui**
    # guards: path traversal (fora de MANIFEST_DIR), circular, missing
    ...
```

Os shims dos 7 verbos foram migrados para compor partials via
`{{include:}}`. `guia-fluxo.{agent,claude}.md` foi simplificado: a secao
"Agent Behavior" (13 itens) foi removida porque cada item achou casa em
um partial ou shim. `guia-fluxo` agora e **referencia pura**: Trigger
Commands com legenda 👤/🤖/👤→🤖, Core Rule, Tool Notes (diferencas
entre hosts), Portability, e um indice "Where Behavior Lives" apontando
para os partials.

## Consequencias

- + **DRY semantico**: a regra de rename de chat existe em 1 arquivo
  por host (`post_cli.agent.md` ou `post_cli.claude.md`); editar muda
  todos os 7 shims de uma vez.
- + **mark_chapter como solucao real para Claude**: o usuario tem
  divisor visivel + ToC em toda transicao de fase, sem depender de
  versao do Claude Code. `/rename` continua tentado como bonus.
- + **`guia-fluxo` virou referencia honesta**: nao compete mais com os
  shims pela mesma instrucao; carrega so o overview.
- + **Build-time, nao runtime**: o `dist/skills/<verb>/SKILL.md`
  permanece self-contained, sem `{{include:` literal. O agente nunca
  ve a diretiva.
- + **Composicao expressiva**: `ready` nao inclui `lock_protocol`
  (handoff puro, nao edita arquivos) — isso fica explicito no body em
  uma linha em vez de "lembre de nao falar de lock aqui".
- + **Path traversal, ciclo e missing-file detectados** em build com
  exit 2 e mensagem clara. 9 testes de mecanismo + 13 testes de
  composicao final em `tests/test_render_includes.py` e
  `tests/test_body_partials.py`.
- - **+71 linhas no renderer** (incluindo docstring, guards, helper).
  Mais codigo a manter na fabrica.
- - **Indireção em build**: editar um partial muda 4+ skills de uma
  vez (pode mascarar regressao se a alteracao nao for revisada no
  contexto de cada shim consumidor). Os testes de composicao mitigam.
- - **Convencao nova a aprender** (`_partials/`, `{{include:}}`).
  Mitigado pelo README em `_partials/` e pelo indice em `guia-fluxo`.

## Alternativas consideradas

- **A) Inlinear tudo no body de cada verbo (status quo do Layout B).**
  Rejeitada: a duplicacao cresce a cada novo host suportado e a cada
  nova regra cross-cutting. Editar a logica de rename hoje exige tocar
  14 arquivos.
- **B) Listar partials no manifest.yaml** (`partials: [post_cli, ...]`
  no verbo). Rejeitada: separa o markdown da composicao; pra entender
  como `feature.claude.md` fica, o leitor olha em 2 arquivos. A
  diretiva inline (`{{include:}}`) mantem a composicao **dentro do
  body** que o autor edita.
- **C) Pre-composicao em tempo de edicao** (script auxiliar que gera
  bodies "completos" antes de commitar). Rejeitada: regride o ganho de
  bodies pequenos; o autor pararia editando o gerado por engano.
- **D) Skill-mae como source-of-truth + auto-load**. Rejeitada: Claude
  Code auto-carrega `guia-fluxo` por description, mas Codex/Antigravity
  nao tem o mesmo mecanismo. O hint "continue using guia-fluxo" no
  shim era fragil — agente esquecia de "voltar".

## Links

- [ADR-0008](0008-layout-b-manifest.md) — Layout B. Esta decisao
  estende o mesmo principio (markdown puro, composicao explicita) um
  nivel acima: agora a composicao acontece entre arquivos, nao so
  dentro de um.
- [ADR-0003](0003-json-maquina-markdown-humano.md) — markdown para
  humano. Partials sao markdown puro; expansao acontece na fabrica.
- D-047 — task de implementacao em 5 fases (infra do renderer,
  catalogo de partials, migracao dos shims, simplificacao da
  skill-mae, testes).
