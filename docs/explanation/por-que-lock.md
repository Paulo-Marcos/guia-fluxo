# Por que travar arquivos

> Decisao canonica sobre o mecanismo de unlock registrada em [ADR-0002](../adr/0002-lock-por-commit-message.md). Este texto cobre o "por que travar" (motivacao); o ADR cobre o "como" (marca por commit-message).

## O problema

Agentes de IA (Claude, Cursor, Codex, Cline, Copilot, etc.) editam codigo livremente. Sem barreira, qualquer "limpeza de codigo" no chat seguinte pode quebrar uma feature que ja estava homologada e em uso real.

O custo nao e o bug introduzido - o agente provavelmente conserta se voce pedir. O custo e:

- **Tempo perdido** ate voce notar que algo parou de funcionar.
- **Confianca corroida** no que esta estavel: "sera que mudou alguma coisa?".
- **Refactor de brinde**: o agente "melhorou" uma feature que voce nao pediu para mexer.

## A solucao: tres camadas de defesa

```
features/registry.yaml     <- fonte da verdade (lista de travas)
bin/check-lock.py          <- CLI: gerencia, valida, roda no hook e no CI
.githooks/commit-msg       <- hook git que rejeita commits violando trava
.github/workflows/         <- CI que rejeita PRs violando trava
   lock-check.yml
docs/                       <- regras para os agentes lerem antes de editar
```

As tres camadas sao **redundantes de proposito**:

1. **Documentacao** - informa o agente do protocolo antes de qualquer edicao. Falha quando o agente nao leu.
2. **Git hook local** (`commit-msg`) - rejeita o commit na sua maquina antes mesmo de subir. Falha quando voce passa `--no-verify` ou o hook nao esta instalado.
3. **CI** (`lock-check.yml`) - rejeita o merge no PR mesmo se o hook local foi pulado. Falha so se voce desabilitar branch protection.

A unica forma de aceitar uma alteracao em arquivo travado e incluir no commit:

```
[unlock:<feature-id>] motivo: <razao curta>
```

Sem isso, o commit nao passa. Com isso, fica registrado para sempre no `git log` - **auditoria automatica**, sem arquivo extra para manter.

## Por que unlock e por commit, nao por sessao

Cada commit precisa da marca, mesmo que voce esteja iterando na mesma feature. Isso e proposital: forca a parar e justificar **cada toque**.

Se o agente esta com pressa e quer "passar batido", a marca aparece no historico e voce ve depois. Se voce esta usando o agente, voce aprovou cada uma das marcas - o sinal nao se perde.

## Quando trava nao e o caminho

A trava e proposital para codigo **estavel e em uso**. Nao trave:

- Codigo em construcao (mude livremente).
- Codigo que voce sabe que vai refatorar essa semana.
- Configuracao volatil (`.env`, `*.config.js`).
- Arquivos de migracao de banco (append-only por natureza).

Ver [convencoes-de-lock.md](convencoes-de-lock.md) para detalhes de granularidade e nomenclatura.

## Lock global de adicao

O template inclui um lock global `adicoes-exigem-autorizacao` com `operations: [add]` e `files: ["*"]`. Resultado: **qualquer arquivo novo exige autorizacao explicita**, exceto caminhos em `lock-ignore.txt`.

Motivo: agentes adoram criar arquivos novos para "organizar". O lock global obriga o agente a pedir antes - mesma postura que o lock de modificacao impoe para edicao.
