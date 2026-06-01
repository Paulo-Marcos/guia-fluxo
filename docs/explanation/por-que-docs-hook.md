# Por que existe um hook de docs no `/finish`

## O problema

Docs apodrecem porque "lembrar de atualizar a documentacao" e uma promessa moral, nao um passo do processo. Tres modos de falha sao classicos em projetos com agente:

1. **Doc invisivel.** A feature mudou o CLI, mas ninguem se lembrou de abrir `docs/reference/cli.md`. Tres meses depois o usuario abre a reference e ela esta desatualizada.
2. **README crystalizado.** O fluxo padrao mudou no codigo mas a capa do projeto continua descrevendo o fluxo antigo. Quem chega pela primeira vez segue o caminho velho.
3. **Decisao sem ADR.** Uma feature embute uma escolha arquitetural (novo arquivo de estado, nova camada) sem registrar o trade-off. Seis meses depois ninguem lembra por que aquela tabela existe.

Confiar em "boa intencao" do agente nao resolve. O incentivo do `finish` e fechar e ir pra proxima - revisar docs e custo sem reward imediato.

## A decisao

Bloquear o `finish` ate o agente registrar o que fez com cada doc candidato. Tirar a decisao do nivel "lembre-se de" e colocar no nivel do schema da task.

Tres elementos:

- **`.ai/docs-map.yaml`** declara os docs vivos do projeto e quando cada um deve ser considerado para atualizacao.
- **`ai.py docs-check`** computa candidatos a qualquer momento e devolve em texto humano ou JSON.
- **`ai.py finish`** chama o mesmo computador antes de fechar e exige `--docs-touched`, `--docs-skip` ou `--docs-checked`.

## Por que mapa declarado, e nao "agente decide do zero"

Duas razoes:

1. **Repetibilidade.** Se a heuristica fica no contexto do agente, ela varia turno a turno - hoje ele lembra de checar o CHANGELOG, amanha esquece. Mapa em YAML e deterministico: os mesmos arquivos modificados sempre disparam os mesmos triggers.
2. **Curadoria humana.** O dono do repo sabe quais docs sao "vivos" e quais sao historicos. O mapa codifica esse conhecimento uma vez, e todo agente futuro herda.

O agente ainda tem espaco para julgar - o trigger `architectural-decision` e propositalmente vago. Mas a moldura e do humano.

## Por que tres triggers

| Trigger | Cobre o caso |
| --- | --- |
| `task-finished` | Docs cumulativos (FEATURES, CHANGELOG). Sempre relevantes. |
| `touched` | Docs acoplados a arquivos especificos (CLI -> docs/reference/cli.md). Disparo barato e preciso. |
| `architectural-decision` | Docs de visao e ADRs. Disparo cego, julgamento delegado ao agente. |

Cobre os tres modos de falha do inicio sem inventar uma quarta categoria.

## Por que bloqueio (e nao apenas aviso)

Aviso amigavel e ignorado em 20% dos turnos no melhor caso. Bloquear o `finish` faz o agente parar, ler, decidir e justificar. O custo da pausa cabe na fronteira do `finish` - que ja e o momento "respire fundo, fechei isso direito?". Aviso fica reservado para projetos sem mapa (no-op).

## Por que `--docs-skip` aceita motivo livre

Forcar opcoes fechadas (`--docs-skip nothing-to-do`) treina o agente a passar o flag automaticamente. Pedir uma frase curta obriga a explicar para o futuro leitor por que aquela revisao acabou em zero atualizacoes. Quando o agente nao tem o que escrever, e sinal de que ele nao olhou.

## Consequencias

- **+** Docs vivos param de apodrecer "por esquecimento".
- **+** O proprio repo dogfooda: `.ai/docs-map.yaml` lista cada doc do projeto.
- **+** `docs-check` standalone vira ferramenta de auditoria fora do `finish`.
- **-** Curva de aprendizado: humano precisa entender mapa + triggers + flags do finish.
- **-** Mapa exige manutencao. Doc novo so entra no controle se for adicionado ao YAML.
- **-** O hook so aciona em `finish`. Mudancas que nunca chegam ao `finish` (work in progress, branch abandonada) escapam.

Aceitamos o trade. A alternativa testada - confiar em CHECKLIST no README - nao funcionou.

## Alternativas consideradas

- **Checklist no README/CONTRIBUTING.** Mesmo modo de falha do problema original: instrucao sem enforcement.
- **Hook so via skill `/finish` (sem CLI).** Skill se desvia facilmente; agente "esquece" o passo. CLI forca o gate.
- **Geracao automatica do diff -> entrada de changelog.** Tentador, mas mistura escopos. Esta feature so abre o palco; geracao automatica de conteudo vira feature futura.

## Links

- ADR: [`docs/adr/0005-docs-hook-no-finish.md`](../adr/0005-docs-hook-no-finish.md)
- How-to: [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md)
- Reference: [`docs/reference/docs-map.md`](../reference/docs-map.md)
