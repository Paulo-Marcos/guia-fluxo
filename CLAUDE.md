# CLAUDE.md

Briefing especifico para Claude Code neste repo. Para detalhes de fluxo, comandos e regras gerais, leia tambem [`AGENTS.md`](AGENTS.md) - eles se sobrepoem em quase tudo. Este arquivo destaca o que muda quando o agente e o Claude Code.

## Resumo

`ai-process-pack` e o repo-mae do pack que voce esta instalando em outros projetos. Aqui o pack se aplica a si mesmo (dogfood). Tudo que voce faria num projeto consumidor - abrir feature/issue, marcar ready, fechar finish - voce faz aqui tambem.

## Skills disponiveis (locais a este projeto)

Quando o usuario digitar uma das shims abaixo, dispare a skill correspondente em `.claude/skills/<verbo>/SKILL.md`. **Nao reimplemente a logica inline** - cada shim ja chama `scripts/ai.py` corretamente.

| Atalho | Skill | Quando usar |
| --- | --- | --- |
| `/feature` | `feature` | Nova capacidade pedida explicitamente. |
| `/issue` | `issue` | Bug, regressao ou divida tecnica curta. |
| `/backlog` | `backlog` | Ideia futura, sem prazo / sem decisao tomada. |
| `/promote` | `promote` | Converter item de backlog em feature/issue ja avaliado. |
| `/ready` | `ready` | Implementacao pronta para validacao humana. |
| `/finish` | `finish` | Validacao confirmada, fechar e (opcional) travar. |
| `/status` | `status` | Inspecao da task atual. |

A skill mae `ai-process` em `.claude/skills/ai-process/SKILL.md` carrega contexto compartilhado. As descriptions foram diferenciadas em F-003 para evitar trigger collision - confie no roteador e nao force uma skill diferente da que o usuario invocou.

## Plataforma

- **OS:** Windows (PowerShell e o shell padrao do usuario). Use sintaxe PowerShell: `$null`, `$env:VAR`, backtick para continuacao, `if ($?)` em vez de `&&`.
- **Bash continua disponivel** via tool Bash para scripts POSIX, mas a documentacao do projeto e os exemplos usam PowerShell.
- **CLI principal:** `.\scripts\ai.ps1 <sub>`. O wrapper localiza o Python e invoca `scripts/ai.py`.

## Regras nao-negociaveis

1. **Toda mutacao de estado passa pelo script.** Nunca edite `.ai/*.json`, `FEATURES.md`, `features/registry.yaml` ou `.ai/chat-title.txt` com Edit/Write. Use o CLI.
2. **Abra demanda antes de codar.** Sem `feature`/`issue`/`backlog`, nao ha rastreabilidade.
3. **`skills/generated/*` e read-only para voce.** Edite `skills/manifest.yaml` e rode `python scripts/render-skills.py`.
4. **Respeite o lock.** `features/registry.yaml` lista travados. Para editar um deles, commit precisa de `[unlock:<feature-id>] motivo: <razao>`. Hook `commit-msg` rejeita o resto.
5. **Nao use `git commit --no-verify`** para passar pelo hook. O proprio prompt do sistema ja proibe pular hooks. Se o hook bloquear, investigue.
6. **Repita `NOME DO CHAT: ...`** sempre que o CLI imprimir essa linha. E como o usuario sabe que voce viu e registrou a etapa. Se a sessao expoe API de renomeacao, aplique tambem.
7. **Nao use `validate` como skill.** Foi deprecado em F-003. Fluxo correto: `ready` -> humano testa em uso real -> `finish`. `validate` continua existindo como subcomando do CLI por compatibilidade, mas nao deve aparecer em sugestoes ao usuario.

## Fluxo padrao por turno

1. `.\scripts\ai.ps1 status` para saber a task atual.
2. Se nao houver, abra `/feature`, `/issue` ou `/backlog add`.
3. Implemente (Edit/Write nos arquivos comuns; siga o how-to do unlock para travados).
4. `.\scripts\ai.ps1 ready <ID> --file <...> --summary "..." --validation "..."` quando o codigo esta pronto, **antes** do usuario validar.
5. Aguarde validacao humana em uso real. So entao `.\scripts\ai.ps1 finish <ID>`.

## Verificacao antes de entregar

Rode estes dois e cole a saida no `--validation`:

```powershell
.\scripts\ai.ps1 doctor
python scripts/render-skills.py --check
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
