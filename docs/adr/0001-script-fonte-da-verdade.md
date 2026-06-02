# ADR-0001: Script Python e a fonte de verdade, nao o agente

- **Status:** Aceita
- **Data:** 2026-05-31

## Contexto

Agentes de IA (Codex, Claude Code, Antigravity, Cursor, Cline) esquecem o que estao fazendo entre turnos. Sintomas observados:

- Reescrevem `FEATURES.md` com formato divergente do anterior.
- Inventam IDs de task (`F-007`) sem checar se ja existem.
- Editam estado em comentario de codigo em vez de arquivo dedicado.
- Mesma tarefa, em ferramentas diferentes, produz formatos diferentes.

Nenhum desses sintomas e culpa de um agente especifico - sao inerentes a confiar em "lembra disso pra mim".

## Decisao

Toda mutacao de estado passa por `core/src/ai.py` (originalmente `scripts/ai.py`, movido em F-011). O agente nunca toca `.ai/*.json` nem `FEATURES.md` diretamente - apenas invoca o script via `core/bin/ai.ps1`/skill. A skill e fina (transporta comando); o motor e o Python.

## Consequencias

- + Determinismo: mesma entrada, mesmo resultado, independente do agente.
- + Auditavel via `git log` - cada mutacao e um commit.
- + Paridade entre agentes de graca: trocar Codex por Claude nao muda comportamento.
- + IDs sequenciais e unicos garantidos pelo contador no script.
- + Operacoes atomicas: `feature` cria task **e** atualiza current **e** imprime titulo do chat **e** escreve `FEATURES.md` numa unica invocacao.
- - Requer Python instalado no projeto consumidor.
- - Se o script tiver bug, todo agente herda o bug (custo absorvido em troca de comportamento previsivel).
- - Skills viram thin wrappers - tentacao recorrente de "implementar logica na skill" precisa ser resistida.

## Alternativas consideradas

- **Cada agente escreve direto no JSON com regras documentadas:** falhou no projeto anterior (`gerador-cortes`) - cada agente entendia as regras diferente.
- **Banco SQLite em vez de JSON:** ganho de consistencia nao compensa custo de dependencia e de auditoria perdida (JSON vai pro git, SQLite nao).

## Links

- Explanation pedagogico: [`../explanation/por-que-script-fonte-da-verdade.md`](../explanation/por-que-script-fonte-da-verdade.md).
- Relacionado: [ADR-0003](0003-json-maquina-markdown-humano.md) (divisao JSON/Markdown).
