# ADR-0011: Repensar o modelo de demanda (tipo x status)

- **Status:** Proposta
- **Data:** 2026-06-06

## Contexto

O pack carrega tres deformacoes no modo como representa uma demanda:

1. **Tipo embutido no prefixo de ID.** `F-NNN`, `I-NNN` e `B-NNN` carregam
   o tipo no proprio identificador. Renomear o tipo de uma demanda exige
   trocar o ID, perdendo rastreio.
2. **Backlog disfarcado de tipo.** `B-NNN` mora em `.ai/backlog.json` e
   tem prefixo proprio - mas conceitualmente backlog e **status**
   ("ideia parqueada, ainda nao triada"), nao um tipo distinto de
   feature/bug. Hoje o pack usa dois arquivos (`backlog.json` e
   `tasks.json`) e dois universos de ID para representar o que na
   verdade e o ciclo de vida de uma unica entidade demanda.
3. **`issue` colide com o sentido guarda-chuva da industria.** Em
   GitHub/Jira/Linear, *issue* e o termo amplo (cobre feature, bug,
   chore). No pack, `issue` foi escolhido como sinonimo restrito de
   **bug/regressao**. Quem chega de fora le `/issue` e espera o sentido
   guarda-chuva; o pack entrega o restrito.

O motor ja modela `kind` e `status` como atributos separados em
`tasks.json` (cada task tem ambos os campos). A interface que os usuarios
veem (CLI, skills, FEATURES.md) e que ainda colapsa os dois eixos.

Trez decisoes pendentes dependem deste modelo:

- **B-017** (estado Planejada): so faz sentido se a demanda for criada
  ja triada, separando ato de criar do ato de iniciar.
- **B-018** (current-task robusto sob chats concorrentes): a robustez
  ideal muda conforme demanda seja ou nao mutavel de tipo.
- **B-011/B-012** (cancel verbo): cancelar precisa entender se backlog e
  status (mudar status para Cancelada) ou tipo (precisa migrar entidade
  entre arquivos).

Decidir agora o modelo evita refatorar o motor duas vezes.

## Decisao

**Adotar `kind` + `status` como eixos ortogonais explicitos da entidade
demanda, com prefixo de ID neutro.**

Especificamente:

1. **Backlog passa a ser status**, nao tipo nem arquivo separado.
   `.ai/backlog.json` e absorvido por `.ai/tasks.json`; itens em backlog
   sao tasks com `status: "Backlog"` e sem implementacao iniciada.
2. **`kind` aceita `feature`, `bug`, `chore`.** O nome `issue` deixa de
   existir como tipo (colisao com sentido guarda-chuva). `bug` cobre o
   que hoje e `issue`; `chore` cobre manutencao sem demanda explicita
   (build/lint/refactor pequeno).
3. **Prefixo de ID neutro: `D-NNN`** (demanda). Renomear tipo de uma
   demanda nao muda o ID. O tipo vira coluna em `tasks.json` (`kind`).
4. **Compat de leitura para IDs legados:** `F-NNN`, `I-NNN`, `B-NNN`
   continuam navegaveis (CLI resolve por aliases em uma migracao
   one-shot), mas geracao nova usa `D-NNN`.

Ciclo de vida do `status` (proposta):

```
Backlog -> Planejada -> Em desenvolvimento -> Aguardando validacao -> Validada
                                            |-> Bloqueada -> (volta)
                                            |-> Cancelada (terminal)
```

`Planejada` (B-017) e `Bloqueada`/`Cancelada` (B-011/B-012/B-013) entram
como status adicionais sem precisar de tipo novo.

## Consequencias

- + **Um arquivo, uma identidade.** `.ai/tasks.json` vira fonte unica;
  backlog deixa de ser universo paralelo. Diff/inspecao ficam triviais.
- + **Renomear tipo nao quebra rastreio.** ID estavel, `kind` mutavel.
- + **Vocabulario alinhado com a industria.** `bug` substitui `issue`
  restrito; quem vem de GitHub/Linear entende sem traducao.
- + **Habilita B-011, B-012, B-013, B-017 sem refactor adicional.** Tudo
  vira transicao de status.
- - **Quebra de superficie.** Skills `feature`/`issue`/`backlog` precisam
  ser repensadas (renomear `issue` -> `bug`?). Compat de gatilhos
  precisa de plano (provavelmente manter `/ai:issue` como alias de
  transicao por uma versao).
- - **Migracao one-shot dos repos consumidores.** `init` precisa rodar
  conversor (`F-NNN` -> `D-NNN-feature`, `I-NNN` -> `D-NNN-bug`,
  `B-NNN` -> `D-NNN-backlog`). Erro de migracao apaga rastreio.
- - **CHANGELOG/relatorios precisam de logica nova** para distinguir
  Added vs Fixed a partir de `kind`, nao do prefixo de ID. Trivial mas
  precisa ser implementado.
- - **ADR registra a direcao, nao implementa.** Quem ler isto e abrir
  uma feature precisa ainda projetar a migracao - alarme: ate o
  refactor sair, motor continua misturando os eixos na superficie.

## Alternativas consideradas

- **Manter o modelo atual.** Rejeitada: B-017/B-018/B-011/B-012/B-013
  todos pedem o mesmo refactor por vias diferentes. Adiar empilha custo.
- **Manter `F`/`I`/`B` mas tornar `kind` mutavel via tabela paralela.**
  Rejeitada: prefixo mente sobre a entidade ("mas o ID diz F!"). Custo
  cognitivo permanente.
- **Renomear so o vocabulario (`issue` -> `bug`) sem absorver backlog.**
  Rejeitada: resolve so 1/3 do problema; backlog continua arquivo
  paralelo. Refactor parcial machuca tanto quanto o estado atual.
- **Adotar terminologia GitHub-like inteira (`issue` como guarda-chuva
  + `labels`).** Rejeitada por enquanto: explode complexidade e arrasta
  o pack para fora do sweet-spot ("processo minimo para 1-3 pessoas").

## Links

- [B-017](../../.ai/backlog.json) - estado Planejada (depende deste ADR).
- [B-018](../../.ai/backlog.json) - current-task concorrente (depende deste ADR).
- [B-011](../../.ai/backlog.json) - cancel/abandon (depende deste ADR).
- [B-012](../../.ai/backlog.json) - verbo cancel (depende deste ADR).
- [B-013](../../.ai/backlog.json) - block/unblock (depende deste ADR).
- [ADR-0001](0001-script-fonte-da-verdade.md) - motor centralizado e o que viabiliza migracao one-shot.
- [ADR-0003](0003-json-maquina-markdown-humano.md) - JSON como fonte; `tasks.json` ja modela `kind`+`status`.
