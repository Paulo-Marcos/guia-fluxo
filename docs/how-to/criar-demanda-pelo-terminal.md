# Como criar uma demanda pelo terminal com a sessao ja nomeada

O launcher `gf` cria a demanda (`feature`/`bug`/`chore`), captura o `D-NNN`
gerado e abre o Claude Code com a sessao **ja nomeada** com o titulo canonico
da demanda — eliminando o rename pos-criacao. E o caminho de entrada pelo
terminal; o slash command in-chat (`/guia:feature` etc.) continua coexistindo
como caminho alternativo.

## Uso

PowerShell (Windows):

```powershell
.\core\bin\gf.ps1 feature "Exportar relatorio em PDF"
.\core\bin\gf.ps1 bug "Login cai com email maiusculo" --context "regressao apos D-040"
.\core\bin\gf.ps1 chore "Subir pytest para 8.x" --status planned
```

Bash (Linux/Mac):

```bash
./core/bin/gf feature "Exportar relatorio em PDF"
./core/bin/gf bug "Login cai com email maiusculo" --context "regressao apos D-040"
```

O primeiro argumento e o verbo (`feature` | `bug` | `chore`), o segundo e o
titulo. **Tudo que vier depois e repassado verbatim ao motor** `guia`
(`--context`, `--origin`, `--status backlog|planned|in-development`,
`--under E-NNN`, `--depends-on D-XYZ`, ...).

### Prompt inicial opcional

Por padrao a sessao abre nomeada e **vazia** (voce digita o primeiro turno).
Para ja mandar um prompt inicial:

```powershell
.\core\bin\gf.ps1 feature "Exportar PDF" -Prompt "Implemente a demanda. Comece pelo endpoint."
```

```bash
./core/bin/gf feature "Exportar PDF" --prompt "Implemente a demanda. Comece pelo endpoint."
```

### So criar, sem abrir o Claude

Util para scripting ou quando o `claude` nao esta no PATH:

```powershell
.\core\bin\gf.ps1 chore "Limpeza de imports" -NoLaunch
```

```bash
./core/bin/gf chore "Limpeza de imports" --no-launch
```

## Como funciona

1. Delega a criacao ao shim vizinho (`guia.ps1` / `guia`), que resolve o Python
   e roda o motor — sem duplicar logica.
2. Le o titulo canonico de `.guia/demand-title.txt` (UTF-8, escrito por
   `set_current_task` na criacao). So confia no arquivo se o `D-NNN` casar com
   a linha `created:` do stdout — defesa contra corrida com criacao paralela;
   senao cai na linha `DEMAND_TITLE=` (ou `CHAT_TITLE=` em engine legado).
3. Abre `claude -n "<titulo canonico>"`. A flag `-n/--name` do Claude Code CLI
   define o display name da sessao (prompt box, picker do `/resume`, titulo do
   terminal).

## Limitacao: Claude-only

Por enquanto o launcher so abre o **Claude Code**. Codex App e Antigravity nao
expoem criar uma thread com titulo via API/flag de CLI, entao nao da pra nomear
a sessao na criacao nessas ferramentas. Nelas, use o caminho in-chat e renomeie
depois — ver [renomear-chat.md](renomear-chat.md) e
[reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md).

> Diferente da D-057, que resolve o rename de uma sessao **ja aberta**: a `gf`
> resolve o nome **na criacao**.
