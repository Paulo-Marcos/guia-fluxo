# Como travar um arquivo

Travas declaram que um conjunto de arquivos esta homologado e nao pode ser editado sem autorizacao explicita. Use quando uma feature foi testada, esta em uso real e voce nao planeja iterar nela no curto prazo.

## Via CLI (recomendado)

```powershell
python bin/check-lock.py lock ingestao-livestream `
    --description "Download e parse de VTT da livestream" `
    backend/app/services/ingestao.py `
    backend/app/domain/vtt_parser.py
```

O script:
- Valida que a feature ainda nao existe no registry.
- Avisa se algum arquivo nao existe no repo (nao bloqueia - util para travar paths que serao criados em sequencia).
- Grava `locked_at` com a data de hoje.
- Reescreve `registry.yaml` mantendo o cabecalho.

## Manualmente

Abra [`features/registry.yaml`](../reference/registry-yaml.md) no editor e adicione:

```yaml
locks:
  - id: ingestao-livestream
    description: Download e parse de VTT da livestream
    locked_at: 2026-05-18
    files:
      - backend/app/services/ingestao.py
      - backend/app/domain/vtt_parser.py
```

Confira:

```powershell
python bin/check-lock.py list
```

## Quando travar e quando NAO travar

Ver [explanation/convencoes-de-lock.md](../explanation/convencoes-de-lock.md).

## Schema completo do `registry.yaml`

Ver [reference/registry-yaml.md](../reference/registry-yaml.md).
