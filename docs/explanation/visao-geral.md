# Visao geral do processo

O guia-fluxo transforma pedidos soltos em demandas rastreaveis usando script deterministico em vez de depender da memoria do agente.

## Pecas e seus papeis

| Peca | Papel |
| --- | --- |
| **Skill** | Interface conversacional. Como o agente entende `/feature`, `/bug`, etc. |
| **Script** (`core/src/guia.py`) | Fonte de verdade e automacao. Todas as mutacoes passam por aqui. |
| **`.guia/*.json`** | Estado legivel por programas. Tasks, backlog, current, reports. |
| **`FEATURES.md`** | Historico legivel por humano. Espelha o JSON em prosa. |
| **`features/registry.yaml`** | Lock de arquivos homologados. |
| **Hooks** | Guarda-corpo opcional para lembrar ou bloquear desvios. |

Cada uma tem responsabilidade distinta e nenhuma sobrepoe a outra. A skill nunca escreve no JSON diretamente - ela chama o script. O JSON nunca e editado a mao - quem altera e o script.

## Modelo de demanda (ADR-0011, entregue em 2026-06-07)

Toda demanda tem dois eixos ortogonais:

- **`kind`**: o tipo. `feature` (capacidade nova), `bug` (defeito ou regressao), `chore` (manutencao sem mudanca de comportamento). Cada um tem emoji proprio em todas as superficies de display: ✨ feature, 🐛 bug, 🧹 chore.
- **`status`**: onde a demanda esta no ciclo de vida. `Backlog` (parqueada), `Planejada` (triada mas nao iniciada), `Em desenvolvimento`, `Aguardando validacao`, `Validada`/`Finalizada`. Estados auxiliares: `Bloqueada` (pausada com WIP) e `Cancelada` (terminal, nao volta).

IDs sao neutros (`D-NNN`) — renomear o `kind` de uma demanda nao muda o ID. IDs legacy (`F-NNN`, `I-NNN`, `B-NNN`) continuam navegaveis. Tasks com `kind=issue` (do mundo pre-Fase-4) sao renderizadas como "Bug (legacy)" com emoji 🐛.

```
Backlog ──┬──> Planejada ──> Em desenvolvimento ──> Aguardando validacao ──> Validada
          │                          ▲    │
          └────── start ────────────>┘    ├──> Bloqueada ──> (volta com unblock)
                                          └──> Cancelada (terminal)
```

## Fluxo recomendado

1. Comece com `/feature`, `/bug`, `/chore` ou `/backlog add`. Use `--status backlog|planned|in-development` para criar ja parqueado/triado.
2. O script cria o ID `D-NNN`, atualiza `.guia/tasks.json`, `.guia/current-task.json` e `FEATURES.md` (exceto se `status=Backlog`, que fica fora do catalogo ate ser promovido).
3. O script sempre imprime `NOME DO CHAT: D-NNN <emoji> - #<statusTag> - <title>` e grava `.guia/chat-title.txt`.
4. O agente repete esse nome no chat e executa a renomeacao real quando a ferramenta expuser API ou comando de sessao.
5. Para itens em backlog: `/promote <id> --kind feature|bug|chore` (avalia + comeca) ou `/start <id>` (atalho, pressupoe triagem feita).
6. Para pausar: `/block <id> --reason "..."` (preserva WIP) ou `/plan <id>` (volta para `Planejada`). Para retomar: `/unblock <id>` ou `/start <id>`.
7. Para cancelar: `/cancel <id> --reason "..."` (terminal).
8. Durante a implementacao, o agente registra arquivos e validacoes.
9. `/ready <ID>` move para `Aguardando validacao` — disparado **pela IA** ao terminar de codar, nao pelo humano (ver [`bodies/ready`](../../core/manifest/bodies/ready.claude.md)).
10. Humano testa em uso real.
11. Antes de fechar, o agente roda `docs-check`: le `.guia/docs-map.yaml` e lista docs vivos a atualizar. Quando ha mapa, o `finish` bloqueia ate o agente registrar `--docs-touched`/`--docs-skip`. Sem mapa, vira no-op. Veja [`por-que-docs-hook.md`](por-que-docs-hook.md).
12. `/finish <ID>` marca `Validada`, sugere `#FINALIZADO` e commita por padrao.
13. Se quiser travar, use `finish --lock --lock-id <slug>`.

`validate` ainda existe como subcomando do CLI por compatibilidade, mas o fluxo recomendado e `/ready` -> `/finish`. O subcomando `issue` foi removido na Fase 4 do ADR-0011 — use `/bug`.

## Por que essa arquitetura

- **Por que script e nao agente livre?** [explanation/por-que-script-fonte-da-verdade.md](por-que-script-fonte-da-verdade.md).
- **Por que travar arquivos?** [explanation/por-que-lock.md](por-que-lock.md).
- **Por que `/promote` exige plano antes?** Ver [how-to/promover-backlog.md](../how-to/promover-backlog.md) - a explicacao esta embutida no fluxo obrigatorio.

## Plugin ou repo?

Desde F-009 (2026-06-01) o pack adota o **layout oficial de plugin Claude Code**. Desde F-011 (B-007, 2026-06-02) o repo-mae separa **fontes em `core/`** (`src/`, `build/`, `manifest/`, `lock/`, `hooks/`, `templates/`) de **buildado em `dist/`** (`.claude-plugin/`, `skills/`, `.agents/skills/`, `bin/`). O marketplace local fica em `dist/.claude-plugin/marketplace.json` apontando o plugin raiz para `dist/`. Os atalhos no Claude saem `/guia:feature`, `/guia:bug`, etc. Codex e Antigravity descobrem via `dist/.agents/skills/guia-<verbo>/SKILL.md` (convencao AGENTS.md, prefixo `ai-` desde F-012 pra evitar colisao com comandos nativos), entao usam `/ai-feature` ou `$ai-feature`. Decisao em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

`dist/bin/` (introduzido em F-012) empacota o motor standalone do plugin: copia exata de `core/src/guia.py`, wrapper `guia.ps1` reescrito pra layout flat (motor lado a lado), e shim POSIX `ai`. O `bin/` do plugin e auto-mapeado pra PATH pelo Claude Code, entao apos o instalador (passo 3 de B-008, ainda nao entregue) copiar `dist/*` pra `.guia-fluxo/` no consumidor, basta digitar `ai status` no terminal de qualquer sessao.

Caminho do roadmap a partir daqui:

1. ~~Estabilizar aqui~~ (feito).
2. ~~Extrair para um repo Git~~ (feito - `guia-fluxo`).
3. ~~Adotar layout oficial de plugin Claude Code~~ (feito em F-009).
4. ~~Reorganizar repo-mae em `core/` + `dist/`~~ (feito em F-011, prepara B-008/B-009).
5. ~~Layout `.guia-fluxo/` no consumidor (B-008)~~ (feito: F-012 entregou renderer + bin standalone; F-013 entregou `install.ps1`/`install.sh`, templates em `dist/templates/`, e smoke test do consumer). Pendente apenas o dogfood Codex/Antigravity do proprio repo-mae (`.agents/skills/` so existe em `dist/`, nao na raiz).
6. Publicar marketplace remoto em `github.com/Paulo-Marcos/guia-fluxo` (B-009).
7. Opcional: adicionar hooks (`core/hooks/hooks.json`) pra automacao de eventos; adicionar MCP server pra exposicao programatica do estado das tasks.
