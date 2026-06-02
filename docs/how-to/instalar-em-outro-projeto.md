# Como instalar em outro projeto

Ainda nao ha instalador automatico (ver [`../ROADMAP.md`](../ROADMAP.md)). Por enquanto, copie manualmente os arquivos do pack para os mesmos caminhos no projeto consumidor.

## Layout do repo-mae

O pack separa **fabrica** (`core/`) de **produto buildado** (`dist/`):

- `core/` - fontes: `core/src/ai.py`, `core/build/render-skills.py`, `core/manifest/manifest.yaml`, `core/lock/check-lock.py`, `core/hooks/commit-msg`, `core/templates/`.
- `dist/` - saida do build (gerada por `python core/build/render-skills.py`): `dist/.claude-plugin/`, `dist/skills/`, `dist/.agents/skills/`.

Refactor consumidor (`.ai-process/` com tudo embutido) chega em B-008. Por enquanto, mirror direto.

## Arquivos a copiar

| Origem (no pack) | Destino (no projeto consumidor) |
| --- | --- |
| `core/src/ai.py` | `core/src/ai.py` |
| `core/bin/ai.ps1` | `core/bin/ai.ps1` |
| `core/build/render-skills.py` | `core/build/render-skills.py` |
| `core/lock/check-lock.py` | `core/lock/check-lock.py` |
| `core/manifest/manifest.yaml` | `core/manifest/manifest.yaml` |
| `core/hooks/commit-msg` | `core/hooks/commit-msg` |
| `core/templates/features/registry.yaml` | `features/registry.yaml` |
| `core/templates/features/lock-ignore.txt` | `features/lock-ignore.txt` |
| `dist/.claude-plugin/plugin.json` | `dist/.claude-plugin/plugin.json` (manifest oficial Claude Code) |
| `dist/.claude-plugin/marketplace.json` | `dist/.claude-plugin/marketplace.json` (catalogo do marketplace local) |
| `dist/skills/*` (output gerado para Claude Code) | `dist/skills/*` |
| `dist/.agents/skills/*` (output gerado para Codex e Antigravity) | `dist/.agents/skills/*` |
| `.claude/settings.json` | `.claude/settings.json` (aponta o marketplace para `./dist`) |
| `docs/` (todo o conteudo) | `docs/` |

> **Claude Code:** ao abrir o projeto consumidor, `.claude/settings.json` aponta para `dist/.claude-plugin/marketplace.json` via `extraKnownMarketplaces.ai-process-pack.source.path = "./dist"`. Claude prompta pra confirmar trust + instalacao do plugin `ai` (com `enabledPlugins` habilitando por padrao). Atalhos `/ai:feature`, `/ai:issue`, etc. ficam disponiveis automaticamente nas sessoes seguintes. Fallback manual: `claude --plugin-dir ./dist` ou `/plugin marketplace add ./dist` + `/plugin install ai@ai-process-pack`.
>
> **Codex e Antigravity:** descobrem via `dist/.agents/skills/` (convencao AGENTS.md) - basta a pasta existir. Sem plugin/marketplace.
>
> Detalhes do layout em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

## Bootstrap

No projeto consumidor:

```powershell
.\core\bin\ai.ps1 init --project-name "nome-do-projeto"
git config core.hooksPath core/hooks
```

O `init` cria os JSONs vazios em `.ai/`, escreve `process.json` com o nome do projeto e zera `chat-title.txt`. O `core.hooksPath` ativa o hook que valida marcas `[unlock:<id>]`.

## Editando skills geradas

Skills sao geradas a partir de `core/manifest/manifest.yaml` (fonte unica para os tres agentes). Para alterar:

1. Edite `core/manifest/manifest.yaml`.
2. Rode `python core/build/render-skills.py` para regenerar `dist/skills/<verbo>/SKILL.md` (output do plugin Claude Code) e `dist/.agents/skills/<verbo>/SKILL.md` (Codex + Antigravity, convencao AGENTS.md).
3. Em CI/hook, use `python core/build/render-skills.py --check` para barrar drift entre o manifest e os arquivos gerados.

Nao edite arquivos sob `dist/skills/<verbo>/` ou `dist/.agents/skills/<verbo>/` a mao - eles sao sobrescritos.

## Verificacao

```powershell
.\core\bin\ai.ps1 doctor
```

Depois, ajuste `.ai/process.json` para os comandos de teste e a politica de lock do seu projeto.
