# Instalacao em outro projeto

Ainda nao ha instalador automatico (ver [`ROADMAP.md`](ROADMAP.md)). Por enquanto,
copie manualmente os arquivos do pack para o projeto consumidor.

## Arquivos a copiar

| Origem (no pack) | Destino (no projeto) |
| --- | --- |
| `scripts/ai.py` | `scripts/ai.py` |
| `scripts/ai.ps1` | `scripts/ai.ps1` |
| `scripts/render-skills.py` | `scripts/render-skills.py` |
| `bin/check-lock.py` | `bin/check-lock.py` |
| `skills/manifest.yaml` | `skills/manifest.yaml` |
| `skills/generated/.agents/skills/*` | `.agents/skills/*` (Codex e Antigravity) |
| `skills/generated/.claude/skills/*` | `.claude/skills/*` |
| `templates/features/registry.yaml` | `features/registry.yaml` |
| `templates/features/lock-ignore.txt` | `features/lock-ignore.txt` |
| `templates/.githooks/commit-msg` | `.githooks/commit-msg` |
| `docs/AI_PROCESS.md` | `docs/AI_PROCESS.md` |
| `docs/PROTOCOL.md` | `features/README.md` |
| `docs/HOOKS.md` | `.githooks/README.md` |

## Bootstrap

No projeto consumidor, depois de copiar:

```powershell
.\scripts\ai.ps1 init --project-name "nome-do-projeto"
git config core.hooksPath .githooks
```

O `init` cria os JSONs vazios em `.ai/`, escreve `process.json` com o nome do
projeto, e zera `chat-title.txt`. O `core.hooksPath` ativa o hook que valida
marcas `[unlock:<id>]` nas mensagens de commit.

## Editando skills

Skills sao geradas a partir de `skills/manifest.yaml` (fonte unica para os tres
agentes). Para alterar:

1. Edite `skills/manifest.yaml`.
2. Rode `python scripts/render-skills.py` para regenerar `skills/generated/`.
3. Em CI/hook, use `python scripts/render-skills.py --check` para barrar drift
   entre o manifest e os arquivos gerados.

Nao edite arquivos sob `skills/generated/` a mao — eles sao sobrescritos.
