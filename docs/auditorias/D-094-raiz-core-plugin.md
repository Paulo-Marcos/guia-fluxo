# D-094 — Auditoria da raiz: separar CORE do PLUGIN e justificar os expostos

- **Task:** [D-094](../../.guia/DEMANDAS.md) — Limpeza: separar core do plugin e justificar expostos
- **Tipo:** diagnóstico + proposta (NÃO executa movimentações estruturais — viram demandas-filhas)
- **Data:** 2026-06-23
- **Restrições honradas:** [ADR-0017](../adr/0017-manter-core-src-flat.md) (não reabrir reorg interna de `core/src/`), descoberta do plugin intacta ([ADR-0006](../adr/0006-plugin-oficial-claude-code.md), [ADR-0015](../adr/0015-plugin-global-first-guia-init.md)).

---

## TL;DR (a conclusão que importa)

A percepção "há arquivos demais na raiz" é compreensível, mas o diagnóstico mostra que **a raiz quase não tem gordura movível**. De ~21 entradas no topo, **apenas 2 são realmente "código do projeto"** (`core/` = CORE, `plugins/` = PLUGIN buildado) e **1 é estado** (`.guia/`). **As outras ~18 são arquivos que GitHub, os agentes de IA e os instaladores de plugin *esperam encontrar na raiz* — movê-las quebra a função, não reduz superfície.**

- O **CORE já está consolidado** num lugar só: `core/`. Não há código de motor espalhado pela raiz.
- O **PLUGIN também já está isolado**: `plugins/guia/` (saída de build).
- A superfície "exposta" da raiz é **majoritariamente convenção irredutível** (README, LICENSE, `.github/`, `AGENTS.md`, `marketplace.json`…), não desorganização.

**Reduções reais e seguras são poucas e pequenas** (resumidas em [Proposta de consolidação](#proposta-de-consolidação)): mover os 3 arquivos de *community health* para `.github/` (−3 no topo) e resolver o `VERSION` órfão (−1). Tudo o mais deve ficar onde está, e este doc registra **por quê**, pra ninguém re-litigar por estética.

---

## 1. Inventário + classificação da raiz

Classificação em 4 baldes (refino do `core|plugin|infra` pedido, separando o que é convenção de docs do que é encanamento puro):

- **CORE** — motor interno do guia-fluxo (fontes).
- **PLUGIN** — artefato gerado/exposto para consumo.
- **ESTADO** — runtime do próprio repo (dogfood).
- **INFRA/DOCS** — encanamento de repositório + convenções que ferramentas/agentes leem na raiz.

| # | Entrada (raiz) | Classe | Por que existe | Por que está exposta na raiz (e pode mover?) |
|---|---|---|---|---|
| 1 | `core/` | **CORE** | Fontes do motor: `src/` (guia.py + `_*`), `build/`, `manifest/`, `lock/`, `hooks/`, `templates/`, `bin/`. Fonte da verdade. | **Fica.** Já é o "lugar só" do core. Reorg interna recusada pela [ADR-0017](../adr/0017-manter-core-src-flat.md). |
| 2 | `plugins/` | **PLUGIN** | Saída de `core/build/render-skills.py`: `guia/.claude-plugin/`, `commands/`, `.agents/skills/`, `bin/`, `templates/`. | **Fica.** É o que o marketplace aponta (`source: ./plugins/guia`). Mover quebra descoberta. |
| 3 | `tests/` | **CORE** (teste) | Suíte do motor (gateia cada commit via `tests.yml`). | **Fica.** Convenção root para test runner. |
| 4 | `.guia/` | **ESTADO** | Estado do dogfood: `DEMANDAS.md`, `tasks.json`, `backlog.json`, `current-task.json`, `process.json`, `docs-map.yaml`, `locks/`. | **Fica.** O motor ancora `.guia/` na raiz do projeto por design; é o mesmo arquivo que apareceria em qualquer consumidor. |
| 5 | `.claude-plugin/` | **PLUGIN (descoberta)** | `marketplace.json` — catálogo do marketplace local (`source: ./plugins/guia`). | **NÃO MOVER.** Path de descoberta crítico ([ADR-0015](../adr/0015-plugin-global-first-guia-init.md)). |
| 6 | `.claude/` | **PLUGIN (descoberta)** | `settings.json` com `extraKnownMarketplaces → "."` (dev-loop: abre o repo já vendo o marketplace). | **NÃO MOVER.** Quebra a auto-descoberta na primeira abertura. |
| 7 | `.github/` | **INFRA** | CI/CD (`workflows/`: tests, render-check, lock-check, release) + templates de issue/PR. | **Fica.** GitHub só lê em `.github/`. |
| 8 | `README.md` | **INFRA/DOCS** | Porta de entrada (humanos). | **Fica.** GitHub renderiza só na raiz. |
| 9 | `LICENSE` | **INFRA** | MIT. | **Fica.** GitHub reconhece o badge/aba de licença só na raiz (ou `.github/`/`docs/`); raiz é o idiomático. |
| 10 | `AGENTS.md` | **INFRA/DOCS** | Briefing canônico cross-agente. | **Fica.** Convenção `AGENTS.md` é root-level por definição. |
| 11 | `CLAUDE.md` | **INFRA/DOCS** | Pointer fino do Claude Code. | **Fica.** Claude Code lê na raiz (e em `~/.claude`). |
| 12 | `llms.txt` | **INFRA/DOCS** | Convenção llms.txt (mapa pra LLMs). | **Fica.** A spec exige raiz (`/llms.txt`). |
| 13 | `CHANGELOG.md` | **INFRA/DOCS** | Keep a Changelog (release). | **Fica.** Convenção root; lido pelo `docs-map`. |
| 14 | `CONTRIBUTING.md` | **INFRA** | Guia de contribuição. | **Movível →** `.github/` (GitHub também lê lá). Candidato de consolidação. |
| 15 | `SECURITY.md` | **INFRA** | Política de segurança. | **Movível →** `.github/`. Candidato de consolidação. |
| 16 | `CODE_OF_CONDUCT.md` | **INFRA** | Código de conduta. | **Movível →** `.github/`. Candidato de consolidação. |
| 17 | `VERSION` | **INFRA** | Arquivo de versão `0.4.0`. | **Órfão:** nenhum código/CI lê (verificado). Versão real vive em `plugin.json` + `marketplace.json`. Candidato a remover ou virar fonte única. |
| 18 | `docs/` | **INFRA/DOCS** | Diataxis + ADRs + auditorias. | **Fica.** |
| 19 | `.gitignore` | **INFRA** | Encanamento git. | **Fica.** Root obrigatório. |
| 20 | `.gitattributes` | **INFRA** | Normalização de linha/atributos. | **Fica.** Root obrigatório. |
| 21 | `.editorconfig` | **INFRA** | Estilo de editor. | **Fica.** Root por convenção. |

**Contagem:** CORE = 2 (`core/`, `tests/`) · PLUGIN = 2 (`plugins/`, `.claude-plugin/`) + 1 dev (`.claude/`) · ESTADO = 1 (`.guia/`) · INFRA/DOCS = 15.

---

## 2. Leitura do diagnóstico

1. **CORE e PLUGIN já estão separados e consolidados.** O pedido "juntar o core num lugar só" **já está atendido** por `core/`. Não existe motor vazando pela raiz — o que vaza é convenção.
2. **A raiz é grande porque é uma raiz de projeto open-source maduro**, não porque está bagunçada. README/LICENSE/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/`.github`/dotfiles são o "mínimo open source" (o próprio repo tem a skill `open-source-readiness` que pede exatamente isso). `AGENTS.md`/`CLAUDE.md`/`llms.txt` são convenções **de raiz por spec** — movê-las é auto-sabotar a descoberta por agentes.
3. **A maioria das movimentações "limpariam" o `ls` ao custo de quebrar função.** O ganho cosmético não paga o risco. Por isso a proposta abaixo é deliberadamente curta.

---

## Proposta de consolidação

Priorizada por **ganho real ÷ risco**. Nenhuma toca `core/src/` (ADR-0017) nem os paths de descoberta (#5, #6).

### P1 — Resolver o `VERSION` órfão *(trivial, baixo risco)*
`VERSION` (`0.4.0`) **não é lido por nenhum código nem CI** (verificado em `core/`, `.github/workflows/`). A versão efetiva vive em `plugins/guia/.claude-plugin/plugin.json` e `.claude-plugin/marketplace.json`. Hoje são **3 cópias do número, sem sincronia automática** → risco de drift.
- **Opção A (recomendada):** remover o `VERSION` da raiz e eleger `plugin.json` como fonte única. −1 no topo, elimina drift.
- **Opção B:** manter `VERSION` como fonte única e fazer o build *ler* dela pra preencher `plugin.json`/`marketplace.json` (mais trabalho; justifica-se só se quiser bump num lugar só).
- **Decisão do dono necessária** (é convenção de release) → vira demanda-filha pequena. **Não executei** por ser escolha, não obviedade.

### P2 — Mover *community health* para `.github/` *(reduz topo em 3, baixo risco)*
GitHub procura `CONTRIBUTING.md`, `SECURITY.md` e `CODE_OF_CONDUCT.md` **tanto na raiz quanto em `.github/`** — mover não quebra os links/avisos automáticos do GitHub.
- **Efeito:** raiz cai de 21 → 18 entradas; o topo passa a expor só README/LICENSE/CHANGELOG/AGENTS/CLAUDE/llms entre os `.md`.
- **Custo:** atualizar referências relativas em `README.md` (§Contribuindo), `AGENTS.md`, `CLAUDE.md`, `docs-map.yaml` (path de `CONTRIBUTING.md`) e o `.github/ISSUE_TEMPLATE/config.yml` se citar. **Não trivial** (toca vários arquivos) → demanda-filha, não execução agora.
- ⚠️ AGENTS.md proíbe *criar* novos LICENSE/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT — isto é **mover** os existentes, compatível, mas convém o dono confirmar.

### P3 — Não fazer (registrado para não re-litigar)
- **Não** mover `AGENTS.md`/`CLAUDE.md`/`llms.txt`/`README.md`/`LICENSE`/`CHANGELOG.md`: convenção de raiz; mover degrada descoberta por humanos e agentes.
- **Não** mover `.claude-plugin/`, `.claude/`, `.github/`, dotfiles: paths fixos de ferramenta.
- **Não** tocar a estrutura interna de `core/src/` — ADR-0017 já decidiu (flat).
- **Não** aninhar `core/`/`plugins/` sob uma pasta-guarda-chuva (ex.: `src/`): quebraria `source: ./plugins/guia` do marketplace e os paths documentados `core/bin/guia.ps1`.

### Observação fora de escopo (candidata a chore própria)
`README.md:9` ainda diz **"Status: v0.1.0"** enquanto `VERSION`/`plugin.json` estão em **0.4.0**. Drift de doc — bom casar com P1.

---

## Encaminhamento

| Item | Ação | Tamanho | Quem decide |
|---|---|---|---|
| P1 | Remover/dedupe `VERSION` (fonte única de versão) | pequena | **dono** (convenção de release) |
| P2 | Mover CONTRIBUTING/SECURITY/CODE_OF_CONDUCT → `.github/` + ajustar refs | média | **dono** (estética × convenção) |
| P3 | Documentado como "não fazer" — sem ação | — | — |
| Extra | Corrigir `README.md:9` v0.1.0 → v0.4.0 | trivial | — |

Esta demanda (D-094) entrega **o mapa e a proposta**. As execuções P1/P2 e o fix do README viram **demandas-filhas/seguintes** conforme o recorte combinado.

---

## Execução (D-097) — desfecho

A execução das propostas foi feita na demanda-filha **D-097** (chore). Resultado:

- **P1 — FEITO.** `VERSION` virou a **fonte única** do número de versão. O dono optou por *manter* o `VERSION` (não removê-lo): o renderer agora lê o `VERSION` e propaga o número para o campo `version` de `plugin.json` e `marketplace.json` (replace cirúrgico; resto à mão). `render --check` acusa drift. Decisão registrada em [ADR-0019](../adr/0019-version-fonte-unica.md); `tests/test_version_sync.py` (6/6); regra 3 do AGENTS.md atualizada.
- **P2 — DROPADO (decisão do dono).** Ao executar, descobriu-se que mover `CONTRIBUTING`/`SECURITY`/`CODE_OF_CONDUCT` para `.github/` **quebra ~15 links relativos internos** desses arquivos (apontam para `docs/`, `LICENSE`, `VERSION`, `.guia/…`), que precisariam virar `../…`. O ganho era cosmético (−3 itens no `ls` da raiz) e a raiz é local **igualmente padrão** e mais discoverável para esses arquivos. Custo/benefício negativo → **mantidos na raiz**. Registrado aqui para não re-litigar.
- **Fix README — FEITO.** `README.md:9` `v0.1.0` → `v0.4.0` (estava em drift com `VERSION`/`plugin.json`).
