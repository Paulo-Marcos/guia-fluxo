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

Continua igual: main verde, teste de regressao no bug, sem mudanca de tela, PR com caminhos que o git nao conferiu. `finish`/`approve` seguem acao do dono. No solo o executor fecha porque o dono ligou o perfil.

## Consequencias

- + Pilot de ponta a ponta: o PR auditado entra, integra e fecha sem clique.
- + O rastro fica: `[unlock:]` no squash e a evidencia do auto-finish na demanda.
- - O dono deixa de ver, antes do merge, a edicao de teste homologado, de workflow e de lockfile. Ve so no historico.
- - Feature fecha sem uso real. O dono testa depois e abre bug se precisar.
- - Projeto com mais de uma pessoa nao deve ligar. O texto da etapa avisa.

## Alternativas consideradas

- **Configurar chave por chave** (`alwaysHumanLocks: []`, `kinds` com feature...). Ja da quase tudo, mas sao quatro decisoes soltas e o `alwaysHuman` nao desligava. Uma chave com nome deixa claro o que se perde.
- **Perfil no `/guia:profile`.** Os perfis so preenchem `delivery` pelos fatos do repo. Ser solo e decisao do dono, nao fato do repo.

## Links

- R6 (autonomia) e R7 (auto-finish) em [`docs/especificacao-entrega-por-pr.md`](../especificacao-entrega-por-pr.md).
