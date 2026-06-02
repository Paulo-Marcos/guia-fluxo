# CLAUDE.md

Briefing especifico para Claude Code neste repo. Para detalhes de fluxo, comandos e regras gerais, leia tambem [`AGENTS.md`](AGENTS.md) - eles se sobrepoem em quase tudo. Este arquivo destaca o que muda quando o agente e o Claude Code.

## Resumo

`ai-process-pack` e o repo-mae do pack que voce esta instalando em outros projetos. Aqui o pack se aplica a si mesmo (dogfood). Tudo que voce faria num projeto consumidor - abrir feature/issue, marcar ready, fechar finish - voce faz aqui tambem.

## Skills disponiveis (plugin oficial Claude Code, namespace `ai`)

O repo-mae **e um plugin Claude Code oficial**: `dist/.claude-plugin/plugin.json` expoe os skills sob namespace `ai`. Quando o usuario digitar uma das shims abaixo, dispare a skill correspondente em `dist/skills/<verbo>/SKILL.md`. **Nao reimplemente a logica inline** - cada shim ja chama `core/src/ai.py` (via `core/bin/ai.ps1`) corretamente.

| Atalho | Skill | Quando usar |
| --- | --- | --- |
| `/ai:feature` | `feature` | Nova capacidade pedida explicitamente. |
| `/ai:issue` | `issue` | Bug, regressao ou divida tecnica curta. |
| `/ai:backlog` | `backlog` | Ideia futura, sem prazo / sem decisao tomada. |
| `/ai:promote` | `promote` | Converter item de backlog em feature/issue ja avaliado. |
| `/ai:ready` | `ready` | Implementacao pronta para validacao humana. |
| `/ai:finish` | `finish` | Validacao confirmada, fechar e (opcional) travar. |
| `/ai:status` | `status` | Inspecao da task atual. |

A skill mae `ai-process` em `dist/skills/ai-process/SKILL.md` carrega contexto compartilhado. As descriptions foram diferenciadas em F-003 para evitar trigger collision - confie no roteador e nao force uma skill diferente da que o usuario invocou.

> `dist/skills/<verbo>/SKILL.md` (Claude Code) e `dist/.agents/skills/<verbo>/SKILL.md` (Codex + Antigravity, convencao AGENTS.md) sao **todos gerados** por `core/build/render-skills.py` a partir de `core/manifest/manifest.yaml`. Nao edite a mao - veja regra 3 abaixo.
>
> **Descoberta automatica:** o repo tem `dist/.claude-plugin/marketplace.json` (catalogo) + `.claude/settings.json` com `extraKnownMarketplaces` apontando para `./dist`. Ao abrir o repo em Claude Code (primeira vez), confirme o prompt de trust + instalacao do marketplace local. Depois disso, `/ai:feature`, `/ai:issue`, etc. ficam disponiveis em todas as sessoes futuras sem flag. Alternativas pra primeira vez: `claude --plugin-dir ./dist` ou rodar `/plugin marketplace add ./dist` + `/plugin install ai@ai-process-pack` manualmente. Detalhes da decisao em [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md).

## Plataforma

- **OS:** Windows (PowerShell e o shell padrao do usuario). Use sintaxe PowerShell: `$null`, `$env:VAR`, backtick para continuacao, `if ($?)` em vez de `&&`.
- **Bash continua disponivel** via tool Bash para scripts POSIX, mas a documentacao do projeto e os exemplos usam PowerShell.
- **CLI principal:** `.\core\bin\ai.ps1 <sub>`. O wrapper localiza o Python e invoca `core/src/ai.py`.

## Regras nao-negociaveis

1. **Toda mutacao de estado passa pelo script.** Nunca edite `.ai/*.json`, `FEATURES.md`, `features/registry.yaml` ou `.ai/chat-title.txt` com Edit/Write. Use o CLI.
2. **Abra demanda antes de codar.** Sem `feature`/`issue`/`backlog`, nao ha rastreabilidade.
3. **Arquivos gerados sao read-only para voce.** `dist/skills/<verbo>/SKILL.md` (output do plugin Claude) e `dist/.agents/skills/<verbo>/SKILL.md` (cross-tool Codex/Antigravity) sao saida de `core/build/render-skills.py`. Edite `core/manifest/manifest.yaml` e rode `python core/build/render-skills.py` (ou `.\core\bin\ai.ps1 render`). `dist/.claude-plugin/plugin.json` so muda pra bump de versao ou ajuste de metadados (name/description/author).
4. **Respeite o lock.** `features/registry.yaml` lista travados. Para editar um deles, commit precisa de `[unlock:<feature-id>] motivo: <razao>`. Hook `commit-msg` rejeita o resto.
5. **Nao use `git commit --no-verify`** para passar pelo hook. O proprio prompt do sistema ja proibe pular hooks. Se o hook bloquear, investigue.
6. **Repita `NOME DO CHAT: ...`** sempre que o CLI imprimir essa linha. E como o usuario sabe que voce viu e registrou a etapa. Se a sessao expoe API de renomeacao, aplique tambem.
7. **Nao use `validate` como skill.** Foi deprecado em F-003. Fluxo correto: `ready` -> humano testa em uso real -> `finish`. `validate` continua existindo como subcomando do CLI por compatibilidade, mas nao deve aparecer em sugestoes ao usuario.

## Fluxo padrao por turno

1. `.\core\bin\ai.ps1 status` para saber a task atual.
2. Se nao houver, abra `/feature`, `/issue` ou `/backlog add`.
3. Implemente (Edit/Write nos arquivos comuns; siga o how-to do unlock para travados).
4. `.\core\bin\ai.ps1 ready <ID> --file <...> --summary "..." --validation "..."` quando o codigo esta pronto, **antes** do usuario validar.
5. Aguarde validacao humana em uso real.
6. **Antes de fechar, rode `.\core\bin\ai.ps1 docs-check`** - lista docs candidatos a atualizar (le `.ai/docs-map.yaml`). Atualize o que fizer sentido. Sem mapa, esse passo vira no-op com aviso.
7. So entao `.\core\bin\ai.ps1 finish <ID> --docs-touched <path>...` ou `--docs-skip "<motivo>"`. O `finish` bloqueia o fechamento se houver candidatos sem registro. Detalhes em [`docs/how-to/manter-docs-atualizados.md`](docs/how-to/manter-docs-atualizados.md).

## Verificacao antes de entregar

Rode estes dois e cole a saida no `--validation`:

```powershell
.\core\bin\ai.ps1 doctor
python core/build/render-skills.py --check
```

Os dois devem sair com codigo 0. Se `render-skills.py --check` falhar, voce esqueceu de regerar - rode sem `--check` e tente de novo.

## Commits

Padrao: `<tipo>: <descricao no imperativo>`.

```
feature: <titulo da demanda>
issue: <titulo da demanda>
chore: <manutencao sem demanda>
```

Para arquivo travado, adicione na mensagem:

```
[unlock:<feature-id>] motivo: <razao curta>
```

So commite quando o usuario pedir explicitamente. Nunca `--no-verify`, `--no-gpg-sign`, nem amend de commit publicado.

## Quando o usuario pedir algo que nao se encaixa

- Pedido vago ("limpa esse codigo aqui") -> abra `/issue` ou `/feature` com contexto curto antes de comecar.
- Pedido enorme ("reestrutura tudo") -> proponha quebrar em demandas menores. Cada demanda = um chat. Backlog absorve as ideias paralelas.
- Pedido que toca arquivo travado -> pare e mostre o que `features/registry.yaml` declara antes de tentar editar.
- Pedido para mexer em `.ai/*.json` direto -> recuse e pergunte o que ele quer alcancar. Provavelmente existe subcomando.

## Onde aprender mais

- Visao geral: [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md)
- Reference completa: [`docs/reference/cli.md`](docs/reference/cli.md)
- Como contribuir (humanos): [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Brief para outros agentes: [`AGENTS.md`](AGENTS.md)
