# Por que o script e a fonte da verdade

> Decisao canonica registrada em [ADR-0001](../adr/0001-script-fonte-da-verdade.md). Este texto e a versao pedagogica - leia o ADR para o resumo objetivo.

## O problema com agentes "livres"

Sem processo, um agente de IA esquece o que esta fazendo entre turnos. Sintomas tipicos:

- Reescreve um arquivo que ja estava certo porque nao lembra do contexto.
- Inventa numeros de task (`F-007`) sem checar se ja existe.
- Edita `FEATURES.md` a mao com formato divergente do resto.
- Cria backlog em comentario de codigo em vez de em arquivo dedicado.
- Esquece de marcar a task como pronta antes de seguir para outra.

Nenhum desses sintomas e culpa do agente especifico. E inerente a confiar em "lembra disso pra mim".

## A inversao

O **script** (`core/src/ai.py`) e a unica coisa que escreve em `.ai/*.json` e `FEATURES.md`. O agente nunca toca nesses arquivos diretamente.

Resultado:

- IDs sao sequenciais e unicos (script controla o contador).
- Formato e identico independente do agente (Codex, Claude, Antigravity).
- Estado e auditavel: voce le o JSON e sabe a verdade, sem interpretar prosa.
- Operacoes sao atomicas: `feature` cria task **e** atualiza current **e** imprime titulo do chat **e** escreve `FEATURES.md` numa unica invocacao.

## A skill como interface, nao como motor

A **skill** existe so para o agente entender que `/feature "X"` significa rodar `.\core\bin\ai.ps1 feature "X"`. Ela nao implementa logica - chama o script.

Isso da paridade entre agentes de graca: trocar Codex por Claude nao muda comportamento, porque o motor e o mesmo Python.

## Implicacao pratica

Quando voce duvidar do estado, **leia o JSON** (`.ai/current-task.json`, `.ai/tasks.json`), nao o `FEATURES.md` nem a memoria do agente. O JSON e a verdade. O markdown e um espelho.

Quando precisar mudar comportamento (novo campo, nova validacao, nova fase), edite `core/src/ai.py`. Nao edite a skill - ela so transporta o comando.
