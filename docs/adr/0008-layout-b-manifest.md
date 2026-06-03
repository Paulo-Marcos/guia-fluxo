# ADR-0008: Manifest em layout B (index YAML + bodies markdown)

- **Status:** Aceita
- **Data:** 2026-06-03

## Contexto

`core/manifest/manifest.yaml` era um arquivo unico de **422 linhas** com
todos os bodies inline em block-literal YAML (`body: |`). Dores reais
observadas e mensuradas em [`docs/auditorias/F-014-core.md`](../auditorias/F-014-core.md)
(Etapa 1 Q2):

- Validar 1 verbo exige scroll em 422 linhas.
- Diff de PR de bodies vira ruido (indentacao YAML + escape de chars).
- Markdown dentro de YAML perde syntax highlight e preview em quase todo
  editor.
- Duplicacao real: agent_skill e claude_skill compartilham ~70% do
  conteudo semantico de varios verbos. Mudar uma flag exige editar
  N x 2 lugares.
- Pegadinhas YAML: chave `on:` parseia como `True` em PyYAML 1.1 (ja
  causou bug no docs hook).

A auditoria avaliou 3 designs (A: 1 YAML por verbo, B: index + bodies
markdown, C: pasta por verbo). O dev **aprovou explicitamente o B**
durante a Etapa 1.

## Decisao

Migrar para layout B:

```
core/manifest/
  manifest.yaml          # index: ~80 linhas (versao + descriptions + body refs)
  bodies/
    ai-process.agent.md
    ai-process.claude.md
    feature.agent.md
    feature.claude.md
    ... (16 arquivos no total, 1 por verbo x target)
```

Schema do manifest (`version: 2`):

```yaml
version: 2
verbs:
  feature:
    description: |
      PRIMARY TRIGGER for /feature ...
    targets:
      agent_skill:
        body_file: bodies/feature.agent.md
      claude_skill:
        body_file: bodies/feature.claude.md
```

- `description` continua **inline** (gatilho que cada host le; manter
  junto evita drift na hora de mexer).
- `body_file` aponta para markdown puro em `bodies/`.
- Path e validado: precisa existir + estar sob `core/manifest/` (recusa
  path traversal).
- Renderer cacheia leituras por path: se dois targets apontarem para o
  mesmo arquivo, o disco e tocado uma vez (shared_body trivial).

`core/build/render-skills.py` ganhou helper `_resolve_body(verb,
target_name, target_spec, body_cache)`. Sintaxe legada (`body: |`
inline) continua aceita para compatibilidade gradual mas o repo-mae
migrou todos os bodies para arquivos.

## Consequencias

- + Cada body vira markdown puro: preview, syntax highlight, diff limpo.
- + Index ficou com ~80 linhas. Scanear descriptions e os verbos
  disponiveis cabe na tela.
- + Bodies viraram unidades independentes. Mover um body para outro
  verbo = mover 1 arquivo + atualizar 1 linha do index.
- + Shared body futuro vira trivial: aponte dois targets para o mesmo
  `body_file`. O cache do renderer ja ignora leituras duplicadas.
- + Saida em `dist/` permanece **byte-identica** ao layout antigo
  (verificado por `render-skills.py --check`). Migracao zero-risco.
- - 17 arquivos novos sob `core/manifest/bodies/`. Compensa pela
  navegabilidade.
- - Renderer ficou ligeiramente mais complexo (helper extra + cache),
  mas com docstring e teste explicitos.

## Alternativas consideradas

- **A) 1 YAML por verbo:** cada arquivo bounded mas perde vista
  panoramica das descriptions juntas (que e onde trigger collision
  surge). Rejeitada porque solta o controle de trigger consolidado.
- **C) Pasta por verbo:** `core/manifest/verbs/feature/{skill.yaml,
  agent.md, claude.md}`. Tudo do verbo no mesmo lugar mas 3 arquivos
  por verbo (21+ no total) e profundidade extra. Rejeitada por excesso
  de indireccao para o ganho marginal sobre B.
- **D) Manter inline:** rejeitada porque nao resolve nenhuma das dores.

## Links

- [Auditoria F-014, Etapa 1 Q2](../auditorias/F-014-core.md)
- [ADR-0003](0003-json-maquina-markdown-humano.md) - JSON para maquina,
  markdown para humano. Layout B aplica o mesmo principio dentro do
  manifest: YAML para estrutura (maquina), markdown para conteudo
  (humano).
- [ADR-0007](0007-arquitetura-modular-core-src.md) - mesma motivacao
  (decompor monolito) aplicada ao motor.
