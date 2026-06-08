# ADR-0003: JSON para maquina, Markdown para humano

- **Status:** Aceita
- **Data:** 2026-05-31

## Contexto

O processo precisa de dois tipos de leitura sobre o mesmo estado:

- **Maquina** (script, hook, CI): precisa parsear sem ambiguidade. Campos tipados. IDs estaveis. Sem prosa.
- **Humano** (review em PR, leitura cronologica, contribuidor novo): precisa entender o "o que", "por que" e "quando" sem instalar nada nem rodar comando.

Tentar um formato unico cobre nenhum dos dois bem:

- YAML "rico" com prosa em blocos: amigavel para leitura, hostil para escrita programatica (espacamento, escapes).
- Markdown estruturado com tabelas: humano le, maquina parseia mal (regex fragil).
- JSON puro: maquina ok, humano sofre (chaves, escapes, sem markup).

## Decisao

Dois espelhos com responsabilidades disjuntas:

- `.guia/*.json` (`tasks.json`, `backlog.json`, `current-task.json`, `process.json`) e a **fonte de verdade legivel por maquina**. So o script escreve. Schema versionado.
- `FEATURES.md` e o **historico legivel por humano**. So o script escreve. E um espelho do JSON em prosa.

Em caso de divergencia, **JSON ganha**: regenerar `FEATURES.md` a partir do JSON e barato; regenerar JSON a partir de prosa nao e.

## Consequencias

- + Cada formato otimiza para sua audiencia sem comprometer a outra.
- + Review em PR ganha: o diff de `FEATURES.md` mostra a narrativa, o diff de `.guia/*.json` mostra o delta exato.
- + Hooks e CI leem JSON com confianca - nada de regex em markdown.
- + Contribuidor novo abre `FEATURES.md` e entende o estado sem rodar comando.
- - **Duas fontes** que precisam ficar em sincronia. Mitigado: so o script escreve - manter sincronia e responsabilidade dele, nao do humano nem do agente.
- - Se alguem editar `FEATURES.md` a mao (agente confuso, merge mal resolvido), a divergencia e silenciosa ate alguem ler o JSON.
- - Schema do JSON precisa versionamento explicito (campo `schemaVersion`) para evolucao futura sem quebrar leitores antigos.

## Alternativas consideradas

- **Markdown como unica fonte:** rejeitado pelo precedente em `gerador-cortes` - parser de markdown vira fonte de bugs sutis (espaco extra, hifen virou bullet diferente).
- **YAML como unica fonte:** mais legivel que JSON mas sofre os mesmos problemas em revisao de PR (whitespace-sensitive, diff ruidoso em arrays).
- **Banco SQLite:** quebra git diff, quebra leitura por humano sem ferramenta, custo de dependencia.

## Links

- [ADR-0001](0001-script-fonte-da-verdade.md) - o script ser a fonte de verdade e o que torna esta divisao viavel.
- Reference do layout: [`../reference/files.md`](../reference/files.md).
