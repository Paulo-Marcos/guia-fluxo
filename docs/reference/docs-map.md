# Reference: `.ai/docs-map.yaml`

Mapa dos documentos vivos do projeto. Lido por `ai.py docs-check` e pelo hook do `ai.py finish` (F-010). Quando ausente, o projeto e tratado como "sem controle de docs" e o hook vira no-op com aviso amigavel.

## Estrutura

```yaml
version: 1

docs:
  - path: <relative path or directory>
    purpose: "<opcional - frase curta do papel do doc>"
    diataxis: <opcional - tutorials | how-to | reference | explanation | adr>
    triggers:
      - event: <task-finished | touched | architectural-decision>
        paths: [<glob>, ...]      # so para `touched`
        hint: "<opcional>"

conventions:
  diataxis: <bool>
  adr_dir: <path>
  changelog: "keep-a-changelog" | "<outro>"
```

## Campos da raiz

| Campo | Tipo | Descricao |
| --- | --- | --- |
| `version` | int | Schema. Atualmente `1`. |
| `docs` | lista | Documentos vivos que o agente deve considerar a cada `finish`. |
| `conventions` | map | Convencoes que o projeto adota; informativo, agente pode usar pra decidir alem do mapa. |

## Campos de cada `docs[i]`

| Campo | Obrigatorio | Descricao |
| --- | --- | --- |
| `path` | sim | Caminho relativo ao root do projeto. Pode ser arquivo (`README.md`) ou diretorio (`docs/adr/`). |
| `purpose` | nao | Mostrado pelo `docs-check` para o agente entender o papel do doc. |
| `diataxis` | nao | Marcador da camada Diataxis (`tutorials`, `how-to`, `reference`, `explanation`) ou `adr`. So informativo. |
| `triggers` | sim | Lista de gatilhos. Basta um casar para o doc virar candidato. |

## Triggers (`docs[i].triggers[j]`)

Use a chave `event:`. Evite `on:` - YAML 1.1 (default do PyYAML) trata `on/off/yes/no` nao-quotados como booleanos, o que silenciosamente quebra o trigger.

### `event: task-finished`

```yaml
- event: task-finished
  hint: "Adicione entrada se a mudanca for visivel pro usuario."
```

Sempre dispara quando uma F-NNN ou I-NNN entra em `finish`. Use para docs cumulativos (`FEATURES.md`, `CHANGELOG.md`, dashboards de roadmap).

### `event: touched`

```yaml
- event: touched
  paths:
    - "scripts/ai.py"
    - "scripts/ai.ps1"
  hint: "Se voce adicionou/mudou subcomando, documente aqui."
```

Dispara quando algum arquivo modificado pela task casa com pelo menos um glob em `paths`. O matching usa `fnmatch.fnmatch` (estilo shell): `*`, `?`, `[abc]`. Globs sao avaliados contra os caminhos relativos ao root.

Fontes consideradas como "arquivo modificado":

1. `task["modifiedFiles"]` (alimentado por `--file` em `ready`/`finish`).
2. `git diff --name-only HEAD` na hora do check.

### `event: architectural-decision`

```yaml
- event: architectural-decision
  hint: "Mudou a forma de pensar do pack? Crie um ADR."
```

Sempre lista o doc como candidato. Cabe ao agente julgar se a feature realmente mudou regra arquitetural. Use para ADRs (`docs/adr/`) e docs de visao (`docs/explanation/visao-geral.md`).

## Campos de `conventions` (opcional)

Informativo. O hook nao bloqueia nada com base nelas, mas o agente pode usar como contexto.

| Campo | Descricao |
| --- | --- |
| `diataxis` | `true` se o projeto segue Diataxis (`tutorials/how-to/reference/explanation`). |
| `adr_dir` | Onde ficam os ADRs (`docs/adr` por convencao). |
| `changelog` | Estilo do changelog (`keep-a-changelog` recomendado). |

## Onde encaixa no fluxo

- `ai.py docs-check [task-id]` - imprime candidatos (texto ou `--json`). Nao muda estado.
- `ai.py finish` - chama o mesmo computador de candidatos; bloqueia se houver candidatos e o agente nao passou `--docs-touched`, `--docs-skip` ou `--docs-checked`.
- Resultado fica gravado em `.ai/tasks.json` no campo `docsReview`.

Veja tambem:
- How-to: [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md)
- Racional: [`docs/explanation/por-que-docs-hook.md`](../explanation/por-que-docs-hook.md)
- ADR: [`docs/adr/0005-docs-hook-no-finish.md`](../adr/0005-docs-hook-no-finish.md)
