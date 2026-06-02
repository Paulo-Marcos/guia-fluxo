# Como destravar um arquivo permanentemente

Use quando uma feature deixou de fazer sentido travar (ex.: voce vai reescrever do zero, ou ela foi descontinuada).

> Para destravar **so neste commit**, voce nao remove a trava - use [editar arquivo travado](editar-arquivo-travado.md) com a marca `[unlock:<id>]`. Remocao permanente e raro.

## Comando

```powershell
python core/lock/check-lock.py unlock ingestao-livestream
```

Isso remove o bloco do `registry.yaml`. Diferente do unlock temporario, **nao exige marca em commit** - voce esta dizendo "essa feature nao precisa mais ser protegida".

## Confirmar

```powershell
python core/lock/check-lock.py list
```

A feature nao deve mais aparecer.
