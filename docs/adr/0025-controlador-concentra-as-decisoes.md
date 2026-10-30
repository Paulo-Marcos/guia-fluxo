# ADR-0025: o controlador coordena as sessoes e concentra as decisoes

- **Status:** Aceita
- **Data:** 2026-10-30
- **Estende:** [ADR-0023](0023-chat-controlador-e-sessoes-executoras.md) (chat controlador e sessoes executoras)

## Contexto

Em 2026-10-30 o dono pediu D-202 a D-209 numa sessao controladora (local_ea02674e), que abriu uma executora para cada. A ADR-0023 ja dizia quem e controlador e quem e executora; faltou o quadro. Atritos medidos nessa sessao:

1. Follow-ups surgiram fora do controlador: a ADR-0023 deixava a executora abrir a sessao da follow-up (D-195..D-197), e cards de sessao apareceram em chats que o dono nao acompanhava.
2. O controlador montou o estado de tudo juntando notas soltas de cada chat - etapa, PR e "com quem esta a bola" nao existiam num lugar so.
3. Perguntas ao dono chegaram uma a uma, por mensagem, cada executora no seu tempo.
4. Sessoes concluidas (Validada, Integrada) ficaram abertas acumulando na barra lateral.
5. Nada limitava quantas executoras abrem ao mesmo tempo - e a tendencia e abrir sessao demais.

## Decisao

O dono decide tudo pela sessao principal; o motor grava o que o controlador precisa ver:

1. **Follow-up e proposta.** A executora cria a demanda nova com `--status planned --from <D-NNN>`: o motor grava `proposedFrom` e copia o controlador da origem para `chat.controller` (sem sessao), e imprime `PROPOSTA: ...`. A executora nao chama `start_session`; so o controlador abre sessoes. Substitui o "executora abrindo uma follow-up" do item 5 da ADR-0023.
2. **Um quadro: `guia controle`.** Por controlador: as executoras abertas (etapa, PR, sessao) e com quem esta a bola - `dono` (pergunta aberta, bloqueada, ou o `next` para no dono), `fila` (o `next` para na fila ou no gerente da fila) ou `executora` (o `next` tem passo, ou para no agente) -, as perguntas abertas, as propostas sem sessao, as sessoes a arquivar e as vagas. `--json` para o chat.
3. **Fila de decisoes na demanda.** `ask D-NNN "<pergunta>" --option ...` grava em `decisions[]` (`id` P1.., pergunta, opcoes, `askedBy`, `askedAt`). O controlador mostra todas juntas e grava a resposta com `answer D-NNN P<n> --quote "<palavras do dono>"`; o motor imprime `LEVE A EXECUTORA: <sessao> <- D-NNN P<n>: o dono disse "..."`. Resposta dada nao se reescreve. A autorizacao continua a da ADR-0023: as palavras do dono, citadas.
4. **Arquivar com o ok do dono.** O quadro lista `ARQUIVE COM OK DO DONO: <sessao> (D-NNN <etapa>)` para executoras de demandas Integrada, Validada, Finalizada ou Cancelada. O controlador pergunta ao dono uma vez, arquiva pelo app (reversivel) e grava `chat D-NNN --archived` (`--unarchived` desfaz).
5. **Teto de executoras.** `controller.maxExecutors` em `.guia/process.json` (padrao 4; valor invalido volta ao padrao). Contam as executoras do controlador fora de Backlog/Planejada e das etapas concluidas, nao arquivadas. Sem vaga, o quadro marca `SEM VAGA` nas propostas e `ACIMA DO LIMITE` no cabecalho; o controlador nao abre sessao e a demanda espera Planejada. E aviso, nao trava: o motor nao ve o `start_session`.

## Consequencias

- + O dono tem um lugar para olhar e responder: o quadro do controlador, com as perguntas juntas.
- + Follow-up nao vira sessao sem o controlador; o teto deixa explicita a escolha de abrir mais uma.
- + A resposta do dono fica gravada na demanda, citada - o repasse nao a dilui.
- - A executora ainda manda uma linha ao controlador depois do `ask` (o motor nao notifica o app).
- - O teto e regra de comportamento: o motor avisa, mas quem abre a sessao e o chat.

## Links

- [ADR-0023](0023-chat-controlador-e-sessoes-executoras.md)
- [ADR-0024](0024-pilot-liga-a-fila.md)
