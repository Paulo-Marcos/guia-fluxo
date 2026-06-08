# ADR-0006: Adotar layout oficial de plugin Claude Code com namespace `ai`

- **Status:** Aceita
- **Data:** 2026-06-01
- **Atualizada por:** F-011 (B-007, 2026-06-02). Repo-mae reorganizado em `core/` (fontes: `core/src/guia.py`, `core/build/render-skills.py`, `core/manifest/manifest.yaml`, `core/lock/check-lock.py`, `core/hooks/commit-msg`, `core/templates/`) + `dist/` (buildado: `dist/.claude-plugin/`, `dist/skills/`, `dist/.agents/skills/`). Os paths originais desta ADR (`scripts/guia.py`, `plugin-src/`, `.claude-plugin/` na raiz, `skills/` e `.agents/skills/` na raiz) sao historicos - leia o resto do texto preservando esse mapeamento. Wrapper `scripts/guia.ps1` permanece como entry point documentado.

## Contexto

Ate F-009, o pack distribuia skills de duas formas paralelas:

- **Stage de distribuicao** em `skills/generated/.claude/skills/` e `skills/generated/.agents/skills/` (copiados pra projetos consumidores).
- **Standalone dogfood** em `.claude/skills/` e `.agents/skills/` na raiz (ativo runtime do proprio repo - introduzido em I-004).

Esse layout funcionava pra Claude Code via standalone (`.claude/skills/`), mas tinha tres problemas:

1. **Foge da convencao oficial.** Claude Code formalizou em 2026 o conceito de **plugin**: diretorio com `.claude-plugin/plugin.json` + `skills/`, `commands/`, `agents/`, `hooks/`, `bin/` na raiz. Plugins permitem `/plugin install`, marketplaces, versionamento e validacao automatica. Standalone `.claude/skills/` so cobre o caso "uma maquina, um projeto" e nao escala pra compartilhar.
2. **Quatro copias do mesmo conteudo.** O render-skills.py emitia o mesmo SKILL.md em quatro locais (stage Claude, stage Agents, raiz Claude, raiz Agents). Cada mudanca no manifest ecoava em 32 arquivos. Drift entre stage e raiz era certeza.
3. **Atalho `/feature` curto era acidental.** No layout standalone, slash commands nao tem namespace - `/feature` so funciona porque nao existe nenhum outro plugin com mesmo verb na sessao. Em projetos consumidores que ja usam `/feature` de outra fonte, o pack quebraria silenciosamente.

Em paralelo, Codex e Antigravity nao tem nocao de "plugin Claude" - eles seguem a convencao **AGENTS.md** (Linux Foundation, 2024) onde skills ficam em `.agents/skills/<verb>/SKILL.md` na raiz, ativadas via `AGENTS.md` ou descoberta de pasta. Esse tree e cross-tool e independe de Claude.

A tese arquitetural confirmada na pesquisa de 2026-05-31 (opcao A+B do roadmap): **tri-agente** com Claude como principal (via plugin oficial), Codex como secundario, Antigravity como terciario. Plugin oficial Claude + `.agents/skills/` cross-tool cobrem todos os tres sem duplicacao.

## Decisao

Adotar o layout oficial de plugin Claude Code documentado em
<https://code.claude.com/docs/en/plugins>, com namespace `ai`. Concretamente:

1. **Manifest oficial em `.claude-plugin/plugin.json`** (raiz do repo) com `name: "ai"`, `description`, `version`, `author`, `homepage`, `repository`, `license`.
2. **Skills geradas em `skills/<verb>/SKILL.md`** na raiz (output oficial do plugin). Os atalhos no Claude saem namespaced: `/guia:feature`, `/guia:issue`, `/guia:backlog`, `/guia:promote`, `/guia:ready`, `/guia:finish`, `/guia:status`.
3. **Source do manifest movido pra `plugin-src/manifest.yaml`.** O diretorio `skills/` na raiz e agora exclusivamente output do plugin oficial - nao mistura source + generated.
4. **Codex + Antigravity continuam em `.agents/skills/<verb>/SKILL.md`** seguindo a convencao AGENTS.md. Esse tree e cross-tool, indepedente do plugin Claude, e ativado pelos arquivos `AGENTS.md`/`CLAUDE.md` na raiz.
5. **scripts/guia.py permanece como motor.** Skills continuam thin wrappers que invocam `.\scripts\guia.ps1 <sub>` (Windows) ou `python scripts/guia.py <sub>` (POSIX). Migrar pra `bin/` do plugin fica como demanda separada.
6. **Diretorios `skills/generated/` e `.claude/skills/` (na raiz) removidos.** Layout antigo aposentado.
7. **Marketplace local autoregistrado pra dogfood.** O repo expoe um catalogo proprio em `.claude-plugin/marketplace.json` (name: `guia-fluxo`) e o `.claude/settings.json` declara `extraKnownMarketplaces` apontando pra ele via `source: { source: "directory", path: "." }` + `enabledPlugins` habilitando `ai@guia-fluxo` por padrao. Resultado: ao abrir o repo em Claude Code (primeira vez), o usuario recebe prompt de trust+install; depois disso, todas as sessoes futuras ja vem com as skills carregadas, sem precisar de `--plugin-dir`. Isso recupera o caso de uso de descoberta automatica que havia sido perdido junto com `.claude/skills/` standalone, agora pelo caminho oficial. **Esse item foi adicionado durante a propria entrega de F-009**, depois de validacao parcial detectar que sem ele o dogfood quebrava (`/finish` retornava `Unknown command`). Absorve a demanda que era rastreada como B-001 no backlog.

O `scripts/render-skills.py` reduziu de 4 destinos para 2: `skills/<verb>/SKILL.md` + `.agents/skills/<verb>/SKILL.md`. Source unica em `plugin-src/manifest.yaml`.

## Consequencias

- + Pack agora e instalavel via `/plugin install` (quando publicado em marketplace), `claude --plugin-dir <path>` (local) e `claude --plugin-url <zip>` (CI).
- + Namespacing `/guia:*` elimina colisao com outros plugins/skills no projeto consumidor.
- + Cobertura tri-agente sem duplicacao: `skills/` cobre Claude, `.agents/skills/` cobre Codex+Antigravity.
- + Source unica em `plugin-src/manifest.yaml`. Renderer emite 16 arquivos (2 destinos × 8 verbs) em vez de 32.
- + Compativel com `claude plugin validate` (validador oficial) - quando submetermos a `claude-community`, o pipeline encontra o layout esperado.
- + Marketplace local autoregistrado (`.claude-plugin/marketplace.json` + `.claude/settings.json`) preserva o caso de uso de descoberta automatica que parecia perdido: abrir o repo em Claude Code prompta o user pra confirmar trust+install e atalhos `/guia:*` ficam disponiveis nas sessoes seguintes sem flag manual.
- - Atalhos no Claude passam de `/feature` (curto) para `/guia:feature` (namespaced). Dois caracteres a mais de digitacao por comando.
- - Primeira abertura do repo em Claude Code exige aceitar trust prompt do projeto + prompt do marketplace local. Depois disso, todas as sessoes futuras funcionam sem flag.
- - Marketplace local com `source: directory` exige Claude Code 2.1.x+. Versoes anteriores nao reconhecem `extraKnownMarketplaces` com source local.
- - Skills antigas em `.claude/skills/`/`skills/generated/` foram removidas - clones antigos do repo precisam regenerar via `python scripts/render-skills.py` apos pull.

## Alternativas consideradas

- **Manter standalone `.claude/skills/` em paralelo ao plugin.** Custo: dobra a area de saida (8 verbs × 3 destinos = 24 arquivos). Beneficio: atalhos `/feature` curtos no dogfood local sem flag. Rejeitada porque (a) drift entre standalone e plugin retornaria, (b) nao escala pra projetos consumidores (mesmo problema do layout antigo), (c) o ganho de UX nao compensa a complexidade. Apos validacao parcial de F-009 detectar quebra de descoberta automatica, em vez de reabilitar standalone preferimos o marketplace local (item 7 da Decisao), que entrega descoberta automatica pelo caminho oficial sem duplicar a saida.
- **Nome de plugin longo `guia-fluxo`.** UX `/guia-fluxo:feature` ficaria verboso pra um comando digitado o tempo todo. Rejeitada por custo de UX.
- **Manter source em `skills/manifest.yaml`, renderizar pra `.claude-plugin/skills/` ou outro path nao-padrao.** Evita o rename do source mas foge do layout oficial - perde compatibilidade com `claude plugin validate` e marketplace. Rejeitada porque a vantagem real do plugin esta exatamente em seguir o layout.
- **Migrar `scripts/guia.py` pra `bin/ai` ja nesta demanda.** Entrega o layout oficial completo de uma vez. Rejeitada por blast radius: mexeria em toda doc, smoke test, wrapper PowerShell e templates. Fica como follow-up isolado.

## Links

- Layout oficial de plugin Claude Code: <https://code.claude.com/docs/en/plugins>
- Reference completa do plugin: <https://code.claude.com/docs/en/plugins-reference>
- Marketplaces e descoberta de plugins: <https://code.claude.com/docs/en/plugin-marketplaces>, <https://code.claude.com/docs/en/discover-plugins>
- Convencao AGENTS.md (cross-tool, Linux Foundation): <https://agents.md/>
- ADR-0001 (script como fonte de verdade): [`0001-script-fonte-da-verdade.md`](0001-script-fonte-da-verdade.md). Esta decisao preserva o ADR-0001 - o motor continua sendo `scripts/guia.py`.
- ADR relacionado de fluxo (I-004) que adicionou `.claude/skills/` na raiz: nao virou ADR por ser fix de mecanismo. Substituido por este.
- Backlog absorvido: B-001 (`.claude-plugin/marketplace.json` + documentar distribuicao) - entregue como item 7 da Decisao desta ADR.
- Demanda: F-009 (esta entrega).
