# ADR-0024: no pilot, o chat que enfileira liga a fila

- **Status:** Aceita
- **Data:** 2026-10-29
- **Muda:** D-098 (`queue run` so do dono) e o ponto 4 da [ADR-0023](0023-chat-controlador-e-sessoes-executoras.md), so no nivel `pilot`

## Contexto

Depois do `queue add`, o item fica parado ate alguem rodar `guia queue run`. Pela D-098 esse alguem e o dono, e o dono vinha abrindo um chat so para isso (pedido de 2026-10-29, dividido em D-202 a D-205). O chat que levou a demanda ate a fila ja sabe que ela terminou.

O que ja existia: `queue run` passa pela fila e sai (`core/src/_executor.py`, `run`). Ele nao fica rodando. O lease com `O_EXCL` e batimento (D-127) garante um executor por repositorio. O botao do painel (D-187) ja sobe `queue run` destacado.

A autorizacao e do dono. Perguntado como ela vira configuracao, entre "chave nova `delivery.queue.autoRun`" e "o nivel pilot ja autoriza", o dono respondeu: "Pilot já autoriza".

## Decisao

1. **No nivel `pilot`, `queue add` liga a fila.** Com o item gravado aprovado e a fila nem pausada nem congelada, o motor le o lease: executor vivo -> nada; sem executor -> sobe `queue run` destacado (`core/src/_executor_spawn.py`, o mesmo spawn do painel), com saida em `.guia/queue/executor-auto.log`. Abaixo do `pilot`, nada muda: a fila e do dono.
2. **`next` religa.** Com a demanda `Na fila` no `pilot`, `guia next` faz a mesma verificacao. Isso cobre o executor que saiu com o item esperando (CI sem resultado no prazo). O chat acompanha com `next` ate `Integrada`. Se o pilot nao fechou (R7), avisa o controlador que o `finish` e do dono.
3. **A ordem fecha a corrida.** Quem enfileira grava o item e so depois le o lease. O executor solta o lease e so depois rele a fila. Se chegou item novo, ele pega o lease de novo e retoma. Um dos dois sempre ve o outro. Dois chats que sobem executor ao mesmo tempo deixam o segundo recusado pelo `O_EXCL`.
4. **O agente continua sem rodar `queue run` por conta propria.** Quem sobe o executor e o motor, sob a regra acima. `pause`/`resume`/`remove`/`priority`, `approve`, `autonomy`, `configure` e `finish` seguem so do dono.

## Consequencias

- + Ninguem abre chat so para integrar: no `pilot`, a demanda vai do `queue add` ao merge sozinha.
- + O `save_task` passou a gravar sob trava e por troca atomica. Chat e executor gravam demandas diferentes ao mesmo tempo sem apagar um ao outro.
- - Muda o sentido do `pilot` para os projetos que ja estao nele: o merge acontece sem o dono rodar nada. Mitigado: e o mesmo merge que o dono ja autorizava ao subir o nivel (auditoria no head, `alwaysHuman`, CI). Quem quer o controle de volta desce para `queue`.
- - Processo destacado: o log fica em `.guia/queue/executor-auto.log`, nao no chat.
- - `GUIA_AUTO_EXECUTOR=off` desliga o spawn (os testes usam). Nao e autorizacao, so um interruptor: abaixo do `pilot` nada sobe de qualquer jeito.

## Alternativas consideradas

- **Chave `delivery.queue.autoRun` no `process.json`, gravada pelo dono:** mais explicita e independente do nivel. O dono preferiu nao ter mais uma chave: o `pilot` ja e o nivel em que a fila integra sem ele.
- **Executor permanente (daemon):** resolveria a corrida de outro jeito, mas exige servico do sistema e supervisao. O executor de passada unica com retomada cobre o caso.

## Links

- D-204 (esta decisao), D-098, D-127 (lease), D-187 e [ADR-0022](0022-painel-local-com-acoes-do-dono.md) (spawn do painel), D-200 (finish automatico no pilot solo).
