# Visao geral do processo

O ai-process-pack transforma pedidos soltos em demandas rastreaveis usando script deterministico em vez de depender da memoria do agente.

## Pecas e seus papeis

| Peca | Papel |
| --- | --- |
| **Skill** | Interface conversacional. Como o agente entende `/feature`, `/issue`, etc. |
| **Script** (`scripts/ai.py`) | Fonte de verdade e automacao. Todas as mutacoes passam por aqui. |
| **`.ai/*.json`** | Estado legivel por programas. Tasks, backlog, current, reports. |
| **`FEATURES.md`** | Historico legivel por humano. Espelha o JSON em prosa. |
| **`features/registry.yaml`** | Lock de arquivos homologados. |
| **Hooks** | Guarda-corpo opcional para lembrar ou bloquear desvios. |

Cada uma tem responsabilidade distinta e nenhuma sobrepoe a outra. A skill nunca escreve no JSON diretamente - ela chama o script. O JSON nunca e editado a mao - quem altera e o script.

## Fluxo recomendado

1. Comece com `/feature`, `/issue` ou `/backlog add`.
2. O script cria o ID, atualiza `.ai/tasks.json`, `.ai/current-task.json` e `FEATURES.md`.
3. O script sempre imprime `NOME DO CHAT: ...` e grava `.ai/chat-title.txt`.
4. O agente repete esse nome no chat e executa a renomeacao real quando a ferramenta expuser API ou comando de sessao.
5. Durante a implementacao, o agente registra arquivos e validacoes.
6. `/ready <ID>` move para `Aguardando validacao`.
7. Humano testa em uso real.
8. Antes de fechar, o agente roda `docs-check`: le `.ai/docs-map.yaml` e lista docs vivos a atualizar. Quando ha mapa, o `finish` bloqueia ate o agente registrar `--docs-touched`/`--docs-skip`. Sem mapa, vira no-op. Veja [`por-que-docs-hook.md`](por-que-docs-hook.md).
9. `/finish <ID>` marca `Validada`, sugere `#FINALIZADO` e commita por padrao.
10. Se quiser travar, use `finish --lock --lock-id <slug>`.

`validate` ainda existe como subcomando do CLI por compatibilidade, mas o fluxo recomendado e `/ready` -> `/finish`.

## Por que essa arquitetura

- **Por que script e nao agente livre?** [explanation/por-que-script-fonte-da-verdade.md](por-que-script-fonte-da-verdade.md).
- **Por que travar arquivos?** [explanation/por-que-lock.md](por-que-lock.md).
- **Por que `/promote` exige plano antes?** Ver [how-to/promover-backlog.md](../how-to/promover-backlog.md) - a explicacao esta embutida no fluxo obrigatorio.

## Plugin ou repo?

Plugin e viavel e provavelmente e o destino ideal quando o processo estabilizar. Ele empacotaria skills, hooks, comandos e instalador. Para agora, este repo usa um pack local porque e mais facil iterar e debugar.

Caminho sugerido (ja registrado no [ROADMAP](../ROADMAP.md)):

1. Estabilizar aqui.
2. Extrair para um repo Git (feito - `ai-process-pack`).
3. Criar instalador que copie `scripts`, `.ai` base, skills e comandos.
4. Opcionalmente transformar em plugin para Codex/Antigravity quando a API de plugin for o melhor encaixe.
