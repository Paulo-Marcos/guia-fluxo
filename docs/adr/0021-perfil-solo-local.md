# ADR-0021: perfil SOLO local - o pilot que nao para no dono

- **Status:** Aceita
- **Data:** 2026-10-20

## Contexto

No `pilot`, o Guia ainda chama o dono em dois pontos (D-193):

1. **Antes do merge.** `autonomy.alwaysHumanLocks` vale `"*"` por padrao: todo PR com `[unlock:]` espera o `approve`. Com a trava de testes (`testes-sao-contrato`), quase todo PR do gerador-cortes parou ali - a maioria dos 32 merges aprovados a mao. E `alwaysHuman: []` nao desliga os caminhos sensiveis: o `or` de `human_reasons` volta para o padrao.
2. **Depois do merge.** O auto-finish (R7) deixa `feature` de fora, e auditoria sem contagem de achados (`--finding`) conta como condicao nao provada.

Para um time essas paradas protegem. Num projeto **solo e local** (so o dono usa e ele reverte se der errado) viram fila de cliques.

## Decisao

Uma chave so do dono, `autonomy.solo: "on"`, gravada pela etapa `autonomy-solo` do `/guia:configure` (o agente nao a liga). Com ela:

1. **`[unlock:]` nao segura a fila.** A marca continua na mensagem do squash (rastro), mas `human_reasons` nao a conta.
2. **Caminhos sensiveis so param se o dono listar.** Sem `alwaysHuman` configurado, a lista fica vazia. Uma lista explicita continua valendo. `alwaysHuman: []` passa a desligar de fato, com ou sem solo (fim do `or`).
3. **A auditoria continua e quem corrige e o agente.** `audit --approve` com achados acima de `maxOpenFindings` e recusado: o agente corrige e audita de novo. No auto-finish, auditoria aprovada no head conta como prova mesmo sem `--finding`.
4. **Feature fecha sozinha.** `feature` entra nos tipos do auto-finish.

5. **Tela e alwaysHuman viram aviso, nao trava (D-200).** No auto-finish, mudanca de tela (`blockIfUiChanged`) e item com `humanReason` (`blockIfAlwaysHuman`) contam como atendidos com `warning: true`. O aviso fica em `finish.warnings` e no resumo ("Revisar depois ..."), que aparece no `status`, no historico e no detalhe do painel. O dono revisa depois.
6. **Varredura da `Integrada` (D-200).** No inicio de cada passada, o executor reavalia as demandas `Integrada` no pilot com o mesmo checklist. O CI da main e lido uma vez, sem esperar. Assim fecha o que integrou antes de o solo ser ligado, ou com a main ainda pendente.

Continua igual: main verde, teste de regressao no bug, auditoria aprovada e caminhos do squash que o git nao conferiu. `finish`/`approve` seguem acao do dono. No solo o executor fecha porque o dono ligou o perfil.

**Por que o bug sem teste continua travando (D-200).** Das demandas que ficaram em `Integrada` antes da D-200 (D-190, D-192, D-193, D-195, D-196), nenhuma parou por falta de teste: todos os bugs traziam o teste no squash. O que segurou foi auditoria sem contagem, `[unlock:]` e `feature` fora dos tipos. A trava custa pouco, porque quem escreve o teste e o agente, antes do `ship`. E e a unica prova de que o defeito nao volta.

## Consequencias

- + Pilot de ponta a ponta: o PR auditado entra, integra e fecha sem clique.
- + O rastro fica: `[unlock:]` no squash e a evidencia do auto-finish na demanda.
- - O dono deixa de ver, antes do merge, a edicao de teste homologado, de workflow e de lockfile. Ve so no historico.
- - Feature fecha sem uso real. O dono testa depois e abre bug se precisar.
- - Mudanca de tela e de caminho sensivel fecha sem olho humano. Fica so o aviso "Revisar depois" na demanda (D-200).
- - Projeto com mais de uma pessoa nao deve ligar. O texto da etapa avisa.

## Alternativas consideradas

- **Configurar chave por chave** (`alwaysHumanLocks: []`, `kinds` com feature...). Ja da quase tudo, mas sao quatro decisoes soltas e o `alwaysHuman` nao desligava. Uma chave com nome deixa claro o que se perde.
- **Perfil no `/guia:profile`.** Os perfis so preenchem `delivery` pelos fatos do repo. Ser solo e decisao do dono, nao fato do repo.

## Links

- R6 (autonomia) e R7 (auto-finish) em [`docs/especificacao-entrega-por-pr.md`](../especificacao-entrega-por-pr.md).
