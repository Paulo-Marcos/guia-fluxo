# Como auditar desbloqueios

Cada `[unlock:<id>]` em commit fica no `git log` para sempre. Auditoria automatica, sem arquivo extra para manter.

## Resumo via CLI

```powershell
python core/lock/check-lock.py audit
```

Saida:

```
Desbloqueios registrados:

  2026-05-18  a1b2c3d  fix: corrige timestamp negativo no parser de VTT
  2026-05-19  e4f5g6h  refactor: extrai validacao de URL do youtube
```

## Auditoria detalhada (com corpo completo do commit)

```powershell
git log --grep "[unlock:" --fixed-strings --pretty=fuller
```

## Filtrar por feature

```powershell
git log --grep "[unlock:ingestao-livestream]" --fixed-strings --pretty=fuller
```
