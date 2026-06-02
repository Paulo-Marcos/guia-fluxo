# Visao geral do processo

O ai-process-pack transforma pedidos soltos em demandas rastreaveis usando script deterministico em vez de depender da memoria do agente.

## Pecas e seus papeis

| Peca | Papel |
| --- | --- |
| **Skill** | Interface conversacional. Como o agente entende `/feature`, `/issue`, etc. |
| **Script** (`core/src/ai.py`) | Fonte de verdade e automacao. Todas as mutacoes passam por aqui. |
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

Desde F-009 (2026-06-01) o pack adota o **layout oficial de plugin Claude Code**. Desde F-011 (B-007, 2026-06-02) o repo-mae separa **fontes em `core/`** (`src/`, `build/`, `manifest/`, `lock/`, `hooks/`, `templates/`) de **buildado em `dist/`** (`.claude-plugin/`, `skills/`, `.agents/skills/`). O marketplace local fica em `dist/.claude-plugin/marketplace.json` apontando o plugin raiz para `dist/`. Os atalhos no Claude saem `/ai:feature`, `/ai:issue`, etc. Codex e Antigravity continuam descobrindo via `dist/.agents/skills/<verbo>/SKILL.md` (convencao AGENTS.md), entao continuam podendo usar `/feature` ou `$feature`. Decisao em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

Caminho do roadmap a partir daqui:

1. ~~Estabilizar aqui~~ (feito).
2. ~~Extrair para um repo Git~~ (feito - `ai-process-pack`).
3. ~~Adotar layout oficial de plugin Claude Code~~ (feito em F-009).
4. ~~Reorganizar repo-mae em `core/` + `dist/`~~ (feito em F-011, prepara B-008/B-009).
5. Layout `.ai-process/` no consumidor (B-008).
6. Publicar marketplace remoto em `github.com/paulosmarcos/ai-process-pack` (B-009).
7. Opcional: adicionar hooks (`core/hooks/hooks.json`) pra automacao de eventos; adicionar MCP server pra exposicao programatica do estado das tasks.
