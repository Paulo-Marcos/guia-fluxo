# ADR-0013: Consolidacao de bodies por verbo via include host-aware

- **Status:** Aceita
- **Data:** 2026-06-08

## Contexto

O Layout B (ADR-0008) deu um arquivo markdown por target: cada verbo
tinha `bodies/<verb>.agent.md` (Codex/Antigravity) e
`bodies/<verb>.claude.md` (Claude Code). O D-047 (ADR-0012) extraiu o
fluxo pos-CLI compartilhado entre verbos em partials — incluindo a
parte host-especifica em `_partials/post_cli.agent.md` /
`_partials/post_cli.claude.md`.

Apos o D-047, comparando `feature.agent.md` e `feature.claude.md`
linha a linha, descobriu-se que a unica coisa **genuinamente
host-especifica** era qual `post_cli` partial incluir. Todo o resto:

- Header (`# Feature Shim` vs `# Feature`) — cosmetico.
- Intro ("Use when human asks..." vs "Create a new feature task...") —
  parafraseado, mesma intencao.
- Comando: placeholder `"<title>"` vs `"$ARGUMENTS"` — o `$ARGUMENTS` e
  uma substituicao automatica de slash command do Claude Code que entra
  em conflito com a regra do `title_context_rules.md` ("synthesize —
  do not pass the raw sentence"). Ou seja: ate o caso aparentemente
  "real" nao era real.
- Linha "Portable fallback (Linux/Mac/sem PowerShell)" so no claude.md
  — arbitrario; Codex agents em Linux tambem se beneficiam dela.
- Verbosidade das flags (linha solta vs bullets) — estilistico.

Resultado: ~150 linhas de duplicacao semantica entre `.agent.md` e
`.claude.md` em 14 verbos, sem motivo funcional. Editar uma frase de
intro exigia mexer em 28 arquivos.

Adicionalmente, os 6 verbos de lifecycle (status, cancel, block,
unblock, plan, start) tinham ficado **fora** do D-047 — ainda usavam
o padrao antigo "Then continue using `guia-fluxo`" ou inline "Depois
repita `NOME DO CHAT`", duplicando regra que ja vivia nos partials.

## Decisao

1. Introduzir uma diretiva nova no renderer:
   `{{include_per_target: <base-sem-sufixo>}}`. O renderer pre-processa
   a diretiva **antes** de `{{include:}}`, substituindo-a por
   `{{include: <base>.<host>.md}}` baseado no target sendo gerado
   (`agent_skill` -> `agent`, `claude_skill` -> `claude`).
2. Consolidar cada par `bodies/<verb>.{agent,claude}.md` em um unico
   `bodies/<verb>.md`. Os 6 lifecycle verbs sao migrados pra partials
   na mesma operacao (estavam atrasados desde o D-047).
3. No `manifest.yaml`, cada verbo aponta `body_file` dos dois targets
   para o mesmo arquivo consolidado. Preserva o `body_file` per-target
   (compativel com `test_every_target_has_body_file` do ADR-0008).
4. `guia-fluxo` recebe tratamento especial: consolidado, mas com secao
   "Tool Notes per Host" explicitando as diferencas que sobrevivem
   (Codex `/feature` vs Claude `/guia:feature`, chat rename per host).
   E referencia, entao mostrar o mapa completo dos hosts e desejavel.

Mapping no renderer:

```python
TARGET_HOST_SUFFIX = {
    "agent_skill": "agent",
    "claude_skill": "claude",
}
```

Pre-processamento:

```python
def _expand_per_target(text, target_name, origin):
    suffix = TARGET_HOST_SUFFIX.get(target_name)
    if suffix is None and INCLUDE_PER_TARGET_RE.search(text):
        sys.exit(2)  # target sem mapping, mas o body usa a diretiva
    ...
```

Exemplo de body consolidado (`bodies/feature.md`):

```markdown
# Feature

Create a new feature task before editing code.

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 feature "<title>" --context "<context>"
```

{{include_per_target: _partials/post_cli}}    ← agent OU claude, decidido em build

{{include: _partials/lock_protocol.md}}

Then continue with the implementation.
```

## Consequencias

- + **Bodies de verbo: 28 -> 14** (-50%). Total em `bodies/` (incluindo
  partials e README): 33 -> 19 (-42%).
- + **Zero duplicacao semantica entre hosts** para os 14 verbos.
  Editar uma frase muda 1 arquivo; o renderer aplica nos 2 outputs.
- + **6 lifecycle verbs (status, cancel, block, unblock, plan, start)
  passaram a usar partials** — antes ainda viviam no padrao "Then
  continue using guia-fluxo" do pre-D-047.
- + **Saida em `dist/` e equivalente ao estado anterior** modulo a
  padronizacao textual que a gente fez de proposito (escolher 1
  redacao canonica em vez de 2 quase-iguais). Nada funcional muda no
  agente.
- + **Renderer extensivel pra novos hosts**: adicionar uma 3a linha em
  `TARGET_HOST_SUFFIX` habilita o sufixo automaticamente.
- + **Tests cobrem o mecanismo** (4 testes em
  `IncludePerTargetTests`) e o invariante de consolidacao (2 testes
  em `SharedBodyCacheTests`).
- - **`{{include_per_target:}}` e a segunda diretiva no renderer.**
  Pequena complexidade extra que precisa ser ensinada (mas o nome e
  bastante explicito).
- - **Bug em uma frase canonica afeta os 2 hosts simultaneamente.**
  Antes, um typo em `feature.agent.md` so atrapalhava Codex/Antigravity.
  Trade-off aceitavel: o ganho de coerencia supera o risco; alem
  disso, os testes de composicao em `test_body_partials.py` pegam
  divergencias estruturais.

## Alternativas consideradas

- **A) Manter 2 bodies por verbo (status quo do Layout B + D-047).**
  Rejeitada: nao resolve a duplicacao gratuita. Cresce a cada novo
  verbo.
- **B) `shared_body:` puro** (ja existe no renderer). Apontar
  `shared_body: bodies/feature.md` resolve a duplicacao, **mas** sem
  uma diretiva host-aware o `post_cli` host-especifico nao tem como
  ser includado dinamicamente. So funcionaria se o body nao tivesse
  nada host-especifico — que nao e o nosso caso. Por isso a Decisao
  (1) e necessaria.
- **C) Variavel `{host}` no `{{include:}}`** (ex.:
  `{{include: _partials/post_cli.{host}.md}}`). Funciona mas mistura
  semantica de template com semantica de include. A diretiva
  dedicada (`{{include_per_target:}}`) deixa o intent explicito.
- **D) Pos-processamento textual no body** (gera 2 bodies em build
  time a partir de 1 source). Rejeitada: regrediria a vantagem de
  "bodies sao markdown puro com preview limpo" — o source teria
  marcacoes ad hoc.

## Links

- [ADR-0008](0008-layout-b-manifest.md) — Layout B. Esta decisao
  reduz N (de 2 arquivos por verbo para 1) dentro daquela arquitetura,
  sem mudar o schema do manifest.
- [ADR-0012](0012-partials-em-bodies.md) — partials via
  `{{include:}}`. Esta decisao adiciona a diretiva irmã
  `{{include_per_target:}}` na mesma camada.
- D-050 — task de implementacao em 4 fases (renderer + auditoria +
  consolidacao + tests).
