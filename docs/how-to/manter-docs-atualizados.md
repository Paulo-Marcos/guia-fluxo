# How-to: Manter os docs atualizados a cada `/finish`

Este pack tem um hook que evita o sintoma classico de "doc apodrecendo": toda vez que uma demanda fecha, o `ai.py finish` consulta `.ai/docs-map.yaml`, lista os documentos vivos que podem precisar de atualizacao e **bloqueia o fechamento** ate o agente declarar o que fez.

Esta receita cobre o fluxo do dia a dia. Para a referencia de campos, veja [`docs/reference/docs-map.md`](../reference/docs-map.md). Para o racional, veja [`docs/explanation/por-que-docs-hook.md`](../explanation/por-que-docs-hook.md).

## 1. Garantir que o projeto tem um mapa

Verifique:

```powershell
Test-Path .ai/docs-map.yaml
```

- Se retornar `True`, o hook esta ativo. Pode pular para a secao 2.
- Se retornar `False`, o projeto nao tem controle de docs. O `finish` continua funcionando, so emite um aviso no stderr. Para ativar, copie o mapa deste repo (`.ai/docs-map.yaml`) e adapte os paths/triggers para a sua estrutura.

## 2. Fluxo padrao por `/finish`

1. Quando o desenvolvedor confirmou que a feature/issue esta validada, rode o check antes de fechar:

   ```powershell
   .\core\bin\ai.ps1 docs-check
   ```

   A saida lista cada doc candidato com:
   - **purpose**: o que aquele doc faz no projeto;
   - **motivo**: por que ele entrou na lista (`task-finished`, `touched: ...`, `architectural-decision`);
   - **hint**: dica curta de como decidir.

2. Para cada candidato, abra o arquivo, leia o trecho relevante e decida:
   - **Tem mudanca a fazer:** edite o arquivo normalmente (Edit/Write).
   - **Nao tem:** registre o motivo na hora de fechar (passo 4).

3. Quando terminar de editar, rode o `finish` declarando o que tocou:

   ```powershell
   .\core\bin\ai.ps1 finish F-010 `
       --docs-touched docs/reference/cli.md `
       --docs-touched CHANGELOG.md `
       --summary "Hook de docs no finish" `
       --validation ".\core\bin\ai.ps1 doctor"
   ```

4. Se a avaliacao concluiu que nenhum doc precisava mudar, passe o motivo:

   ```powershell
   .\core\bin\ai.ps1 finish F-010 --docs-skip "feature interna, sem impacto em fluxo, comandos ou arquitetura"
   ```

   Tambem da pra misturar:

   ```powershell
   .\core\bin\ai.ps1 finish F-010 `
       --docs-touched CHANGELOG.md `
       --docs-skip "demais candidatos nao se aplicam"
   ```

5. O `finish` registra o resultado em `.ai/tasks.json` no campo `docsReview`:

   ```json
   "docsReview": {
     "candidates": [...],
     "touched": ["CHANGELOG.md", "docs/reference/cli.md"],
     "skipped": "demais candidatos nao se aplicam",
     "checkedAt": "2026-06-01"
   }
   ```

## 3. O que faz um doc aparecer na lista

Tres tipos de trigger no `.ai/docs-map.yaml`:

| Trigger | Quando dispara |
| --- | --- |
| `task-finished` | Toda task finalizada (F-NNN ou I-NNN). Use para FEATURES.md, CHANGELOG.md, dashboards. |
| `touched` (com `paths:`) | Quando um dos arquivos modificados pela task casa com algum glob (`fnmatch`). Use para docs acoplados a codigo. |
| `architectural-decision` | Sempre lista. Cabe ao agente julgar se a feature realmente mexeu em arquitetura. Use para ADRs e docs de visao. |

## 4. Adicionar um doc novo ao controle

1. Edite `.ai/docs-map.yaml`.
2. Adicione uma entrada em `docs:` com `path`, `purpose` e um ou mais `triggers`.
3. Rode `.\core\bin\ai.ps1 docs-check` para conferir que aparece com a razao certa.

Lembre que o proprio `.ai/docs-map.yaml` esta nos paths dos triggers de CLAUDE.md/AGENTS.md neste repo - mexer no mapa lista esses dois como candidatos no proximo `finish`.

## 5. Quando voce decide pular o hook

So existe um caminho legitimo: o projeto nao tem (e nao quer ter) controle de docs. Nesse caso, `.ai/docs-map.yaml` simplesmente nao existe e o hook vira no-op. Nao tente burlar com `--docs-skip "n/a"` sem ler os candidatos - voce ou um agente futuro vai pagar a divida de docs depois.
