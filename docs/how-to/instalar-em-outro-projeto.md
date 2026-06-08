# Como instalar em outro projeto

Desde F-013 (2026-06-02) o pack tem **instalador oficial**: `install.ps1` (Windows) e `install.sh` (Linux/Mac). O instalador copia `dist/` (build do repo-mae) para o layout final no projeto consumidor e roda `ai init` pra semear `.guia/`.

## TL;DR

```powershell
# Windows
git clone https://github.com/paulosmarcos/guia-fluxo C:\dev\guia-fluxo
cd C:\dev\meu-projeto
C:\dev\guia-fluxo\install.ps1
```

```bash
# Linux/Mac
git clone https://github.com/paulosmarcos/guia-fluxo /opt/guia-fluxo
cd /path/to/meu-projeto
/opt/guia-fluxo/install.sh
```

## Layout final no consumidor

```
<projeto-consumidor>/
├── .guia-fluxo/                    plugin Claude (tudo numa pasta, seguro pra rm -rf)
│   ├── .claude-plugin/             manifest do plugin + marketplace
│   ├── bin/                        motor standalone (guia, guia.ps1, guia.py) - vira PATH no Claude
│   └── skills/                     skills do plugin (namespace ai:)
├── .agents/                        externo ao .guia-fluxo/ (convencao AGENTS.md)
│   └── skills/ai-*/                cross-tool Codex + Antigravity (prefixo ai-)
├── .githooks/commit-msg            hook git para validar [unlock:<id>] (opcional)
├── features/registry.yaml          lock de arquivos homologados (opcional)
├── features/lock-ignore.txt        excecoes do lock (opcional)
├── .guia/                            estado da maquina (process, tasks, backlog)
└── FEATURES.md                     catalogo legivel (criado no primeiro `feature`)
```

## Flags do instalador

| Flag (PS) | Flag (sh) | Efeito |
| --- | --- | --- |
| `-Target <path>` | `--target <path>` | Onde instalar. Default: diretorio atual. |
| `-DryRun` | `--dry-run` | Mostra o que seria copiado, nao escreve nada. |
| `-Force` | `--force` | Sobrescreve `.githooks/`, `features/registry.yaml` e `features/lock-ignore.txt` se ja existirem. Por padrao, **preserva** customizacoes do consumidor. |
| `-SkipInit` | `--skip-init` | Nao chama `ai init` no final. Use se for rodar manualmente com flags. |

`-DryRun` recomendado na primeira tentativa, pra revisar o mapa de copia antes.

## O que e idempotente

Re-rodar o installer e seguro:

- `.guia-fluxo/` e `.agents/skills/` sao **substituidos** pelo build atual (sao "produto", nao customizaveis).
- `.githooks/commit-msg` e `features/*` sao **preservados** se ja existirem (use `-Force` pra sobrescrever).
- `.guia/*.json` e `FEATURES.md` sao preservados pelo proprio `ai init` (que nao destroi estado existente).

## Ativando o hook git no consumidor

Apos o install:

```powershell
git config core.hooksPath .githooks
```

Isso ativa o `commit-msg` que valida `[unlock:<id>]` antes de aceitar commits que mexem em arquivos travados.

## Verificacao

```powershell
# Windows
python .guia-fluxo/bin/guia.py doctor
# ou direto via shim se .guia-fluxo/bin/ estiver no PATH (Claude faz automatico)
ai doctor
```

```bash
# Linux/Mac
python3 .guia-fluxo/bin/guia.py doctor
# ou
.guia-fluxo/bin/ai doctor
```

Esperado: `Guia Fluxo files OK.`

## Como atualizar para uma nova versao do pack

```powershell
cd C:\dev\guia-fluxo
git pull
python core/build/render-skills.py    # rebuilda dist/
cd C:\dev\meu-projeto
C:\dev\guia-fluxo\install.ps1    # re-instala (substitui .guia-fluxo/ e .agents/)
```

Suas customizacoes em `.githooks/commit-msg`, `features/registry.yaml`, `features/lock-ignore.txt` e `.guia/` sao preservadas.

## Como desinstalar

```powershell
Remove-Item -Recurse -Force .guia-fluxo
Remove-Item -Recurse -Force .agents/skills
# opcional, se quiser remover hook git e lock:
git config --unset core.hooksPath
Remove-Item .githooks/commit-msg
Remove-Item -Recurse features
```

Estado do processo (`.guia/`, `FEATURES.md`) e dados seus — apague separadamente se quiser zerar tudo.

## Quem descobre o que

| Agente | Como descobre o pack | Comandos |
| --- | --- | --- |
| Claude Code | Plugin em `.guia-fluxo/.claude-plugin/plugin.json` (auto-detectado quando abre o projeto). | `/guia:feature`, `/guia:issue`, `/guia:status`, etc. |
| Codex CLI | Convencao AGENTS.md: le `.agents/skills/ai-*/SKILL.md`. | `/ai-feature`, `/ai-issue`, etc. |
| Antigravity | Mesma convencao do Codex (AGENTS.md). | `$ai-feature`, `$ai-issue`, etc. |

Detalhes da decisao em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

## Sem instalador (rota copia-manual, ainda suportada)

Se voce nao quiser usar `install.ps1`/`install.sh` (ex.: ambiente sem PowerShell e sem bash), faca a copia manual seguindo o mapa:

| Origem (em `dist/`) | Destino (no consumidor) |
| --- | --- |
| `dist/.claude-plugin/` | `.guia-fluxo/.claude-plugin/` |
| `dist/skills/` | `.guia-fluxo/skills/` |
| `dist/bin/` | `.guia-fluxo/bin/` |
| `dist/.agents/skills/` | `.agents/skills/` |
| `dist/templates/.githooks/commit-msg` | `.githooks/commit-msg` |
| `dist/templates/features/registry.yaml` | `features/registry.yaml` |
| `dist/templates/features/lock-ignore.txt` | `features/lock-ignore.txt` |

Depois rode `python .guia-fluxo/bin/guia.py init --project-name <nome>` no consumidor.

## Editando skills (so faz sentido se voce e o mantenedor do pack)

Skills sao geradas a partir de `core/manifest/manifest.yaml` no repo-mae. Para alterar:

1. Edite `core/manifest/manifest.yaml` (no repo do pack, nao no consumidor).
2. Rode `python core/build/render-skills.py` (regenera `dist/skills/`, `dist/.agents/skills/`, `dist/bin/`, `dist/templates/`).
3. Em CI, use `python core/build/render-skills.py --check` para barrar drift.
4. Re-instale no consumidor com `install.ps1`/`install.sh`.

Nao edite arquivos sob `dist/` a mao — sao sobrescritos pelo render. No consumidor, nunca edite `.guia-fluxo/` a mao — sobrescritos pelo installer.
