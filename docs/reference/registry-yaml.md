# Reference: `features/registry.yaml`

Fonte da verdade da lista de travas.

## Estrutura

```yaml
locks:
  - id: ingestao-livestream
    description: Download e parse de VTT da livestream
    locked_at: 2026-05-18
    operations: [add, modify, delete, rename]
    files:
      - backend/app/services/ingestao.py
      - backend/app/domain/vtt_parser.py
```

## Campos

| Campo | Obrigatorio | Tipo | Descricao |
| --- | --- | --- | --- |
| `id` | sim | string | Slug kebab-case unico. Usado em `[unlock:<id>]`. |
| `description` | sim | string | Curta. Descreve a funcionalidade protegida. |
| `locked_at` | sim | date | Quando a trava foi adicionada. O CLI grava automaticamente. |
| `operations` | nao | list[string] | Operacoes que a trava bloqueia. Default: tudo (equivale a lock total). |
| `files` | sim | list[path] | Arquivos protegidos. Aceita glob. |

## Operacoes aceitas

- `add` - criar/adicionar arquivo.
- `modify` - alterar arquivo existente.
- `delete` - remover arquivo.
- `rename` - renomear/mover arquivo.

Locks antigos sem o campo `operations` continuam como **lock total** (todas as operacoes bloqueadas).

## Exemplos

### Lock total

```yaml
- id: exemplo-total
  description: Protege feature inteira
  operations: [add, modify, delete, rename]
  files:
    - frontend/src/foo.tsx
```

### Lock so de remocao (contrato publico)

```yaml
- id: exemplo-so-remocao
  description: Nao remover contrato publico
  operations: [delete, rename]
  files:
    - backend/app/domain/contrato.py
```

### Lock global de adicao

O template inclui um lock global que bloqueia `add` em `*`. Resultado: qualquer arquivo novo exige autorizacao explicita, exceto caminhos em `lock-ignore.txt`.

```yaml
- id: adicoes-exigem-autorizacao
  description: Toda adicao nova requer aprovacao
  operations: [add]
  files:
    - "*"
```

## `lock-ignore.txt`

Lista de paths que **nunca** devem ser travados. Um path por linha. Default:

```text
.gitignore
features/lock-ignore.txt
```

Isso garante que mesmo o lock global `adicoes-exigem-autorizacao` nao bloqueie esses arquivos.

## Validacao

```powershell
python core/lock/check-lock.py list                # lista travas
python core/lock/check-lock.py check <arquivo>     # exit 1 se travado
```
