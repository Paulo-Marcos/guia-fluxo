# ai-process-pack

Processo portavel para agentes de IA (Codex, Claude, Antigravity e similares) transformarem
pedidos soltos em demandas rastreaveis: backlog, status, validacao, finalizacao e lock
de funcionalidades homologadas. Inteligencia conversacional via skills; fonte de verdade
em scripts deterministicos + arquivos JSON/YAML.

> **Status:** v0.1.0. Extracao inicial do projeto `gerador-cortes`. Layout estabilizando;
> instalador ainda nao escrito (ver Roadmap).

## Por que existe

Sem processo, o agente esquece o que esta fazendo entre turnos, perde rastreabilidade de
quais arquivos foram tocados em qual demanda, e nao consegue proteger funcionalidades
homologadas contra refactor de brinde. Este pack resolve isso com:

- **Skill** = interface conversacional (`/feature`, `/issue`, `/backlog`, `/promote`, `/ready`, `/finish`, `/status`).
- **Script** = fonte de verdade e automacao (`scripts/ai.py`).
- **`.ai/*.json`** = estado legivel por programas.
- **`FEATURES.md`** = historico legivel por humano.
- **`features/registry.yaml`** = lock de arquivos homologados.
- **Hooks git** = guarda-corpo opcional para validar commits.

Leia [`docs/AI_PROCESS.md`](docs/AI_PROCESS.md) para o desenho completo do processo.

## Layout do repositorio

```
ai-process-pack/
├── README.md                ← este arquivo
├── VERSION                  ← SemVer (lido pelo CLI; futuro `ai --version`)
├── CHANGELOG.md             ← Keep a Changelog
├── scripts/
│   ├── ai.py                ← motor CLI (Python 3.10+)
│   └── ai.ps1               ← wrapper PowerShell que localiza Python
├── bin/
│   └── check-lock.py        ← validador de locks usado pelo hook commit-msg
├── skills/
│   ├── agents/              ← skills para Codex/Antigravity (.agents/skills/)
│   │   └── {ai-process,feature,issue,backlog,promote,ready,finish,status}/
│   └── claude/
│       ├── skills/          ← skill para Claude (.claude/skills/)
│       └── commands/        ← slash commands do Claude (.claude/commands/)
├── templates/               ← seeds copiados pelo instalador
│   ├── features/
│   │   ├── registry.yaml    ← inclui lock global "adicoes-exigem-autorizacao"
│   │   └── lock-ignore.txt
│   └── .githooks/
│       └── commit-msg
└── docs/
    ├── AI_PROCESS.md        ← desenho do processo, fluxo, comandos
    ├── PROTOCOL.md          ← protocolo de lock de funcionalidades
    └── HOOKS.md             ← uso dos hooks git
```

Tudo que o `ai init` regera (process.json, tasks.json, backlog.json, current-task.json,
chat-title.txt) nao vai em `templates/` porque o motor cria sob demanda.

## Como funciona (visao rapida)

No projeto consumidor, depois de instalado:

```powershell
.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\scripts\ai.ps1 issue "Bug observado" --context "Sintoma e impacto"
.\scripts\ai.ps1 backlog add "Ideia futura"
.\scripts\ai.ps1 promote B-001 --kind feature --assessment "Claro" --plan "Plano curto"
.\scripts\ai.ps1 status
.\scripts\ai.ps1 ready F-016 --file scripts/ai.py --summary "Implementacao pronta"
.\scripts\ai.ps1 finish F-016 --lock --lock-id ai-process-pack
```

Cada comando atualiza `.ai/tasks.json`, `.ai/current-task.json`, `FEATURES.md` e imprime
um titulo sugerido (`NOME DO CHAT: F-016 - #DEV - Titulo`) que o agente repete no chat
e tenta aplicar via API/comando da ferramenta quando disponivel.

## Instalacao em outro projeto

Ainda nao ha instalador. Por enquanto, copie manualmente:

| Origem (no pack) | Destino (no projeto) |
| --- | --- |
| `scripts/ai.py` | `scripts/ai.py` |
| `scripts/ai.ps1` | `scripts/ai.ps1` |
| `bin/check-lock.py` | `bin/check-lock.py` |
| `skills/agents/*` | `.agents/skills/*` |
| `skills/claude/skills/*` | `.claude/skills/*` |
| `skills/claude/commands/*` | `.claude/commands/*` |
| `templates/features/registry.yaml` | `features/registry.yaml` |
| `templates/features/lock-ignore.txt` | `features/lock-ignore.txt` |
| `templates/.githooks/commit-msg` | `.githooks/commit-msg` |
| `docs/AI_PROCESS.md` | `docs/AI_PROCESS.md` |
| `docs/PROTOCOL.md` | `features/README.md` |
| `docs/HOOKS.md` | `.githooks/README.md` |

Depois, no projeto consumidor:

```powershell
.\scripts\ai.ps1 init --project-name "nome-do-projeto"
git config core.hooksPath .githooks
```

O `init` cria os JSONs vazios, escreve `process.json` com o nome do projeto, e zera
`chat-title.txt`. O `core.hooksPath` ativa o hook que valida marcas `[unlock:<id>]`
nas mensagens de commit.

## Roadmap

- **v0.2** — Instalador (`install/install.ps1`) que copia tudo e roda `ai init` numa
  unica invocacao, com flag `--upgrade` que preserva estado.
- **v0.3** — Suporte Unix (`bin/ai.sh`, `install/install.sh`).
- **v0.4** — `ai --version` lendo de `VERSION`; campo `packVersion` em `process.json`
  para rastrear qual versao do pack cada projeto consome.
- **v1.0** — Cobertura de testes minima (smoke do CLI) e documento de migracao entre
  versoes do pack.

## Licenca

A definir.
