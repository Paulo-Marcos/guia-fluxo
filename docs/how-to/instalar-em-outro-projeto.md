# Como instalar em outro projeto

## Claude Code: sem clone (rota recomendada)

Desde D-075 (2026-06-16) o plugin é **autossuficiente** no Claude Code — não precisa clonar o repo nem rodar instalador. Pré-requisito: **Python 3.10+** no PATH. No projeto consumidor:

```
/plugin marketplace add Paulo-Marcos/guia-fluxo
/plugin install guia@guia-fluxo
```

O motor vai embutido no plugin e as skills o invocam via `${CLAUDE_PLUGIN_ROOT}/bin/guia.py` (caminho absoluto à instalação, não relativo ao CWD). Ele se ancora no projeto onde você está e **cria o `.guia/` sozinho no primeiro comando** — sem `init` manual. Os únicos arquivos que aparecem no consumidor são o estado `.guia/` (+ `FEATURES.md`).

**Atualizar** para uma nova versão: `/plugin marketplace update guia-fluxo` + `/plugin update guia@guia-fluxo`. O Claude detecta a atualização pela **versão** do plugin, então o pack precisa ter bumpado `VERSION`/`plugin.json`/`marketplace.json` para a nova versão ser puxada.

### Ativando locks no Claude (opcional): `/guia:init`

Por padrão o plugin só cria o `.guia/`. Para ligar os **locks** de arquivo, rode `/guia:init` uma vez. Ele:

1. semeia o `.guia/` (idempotente);
2. deploya `features/registry.yaml`, `features/lock-ignore.txt` e `.githooks/commit-msg` do `templates/` do plugin (`${CLAUDE_PLUGIN_ROOT}/templates/`), sem sobrescrever o que já existir;
3. configura `git core.hooksPath .githooks` — **só se ainda não estiver definido**.

`--no-locks` faz só o seed do `.guia/`; `--force` sobrescreve. O `commit-msg` é robusto: acha o validador em `${CLAUDE_PLUGIN_ROOT}/bin/check-lock.py` quando o commit roda dentro de uma sessão Claude e **degrada com aviso** (libera o commit sem checar) se não achar — ou seja, os locks valem dentro do Claude Code; num terminal puro fora da sessão eles não são aplicados.

> **Já usa `core.hooksPath` próprio (Husky etc.)?** O `init` **não** sobrescreve — ele só configura o hooksPath se ainda não houver um. Nesse caso, copie o `.githooks/commit-msg` do plugin para a sua pasta de hooks à mão para somar a checagem de locks.

## Codex / Antigravity / dev: cópia manual

Os instaladores `install.ps1`/`install.sh` foram **descontinuados** (D-082): apontavam para o antigo `dist/` (renomeado para `plugins/guia/` no D-076) e o modelo copia-pro-projeto contraria o global-first. Para hosts que leem `.agents/skills/` (Codex, Antigravity) ou para desenvolver o motor, copie manualmente a partir do clone do pack:

| Origem (em `plugins/guia/`) | Destino (no consumidor) |
| --- | --- |
| `plugins/guia/.claude-plugin/` | `.guia-fluxo/.claude-plugin/` |
| `plugins/guia/commands/` | `.guia-fluxo/commands/` |
| `plugins/guia/bin/` | `.guia-fluxo/bin/` |
| `plugins/guia/.agents/skills/` | `.agents/skills/` |
| `plugins/guia/templates/.githooks/commit-msg` | `.githooks/commit-msg` (opcional, locks) |
| `plugins/guia/templates/features/registry.yaml` | `features/registry.yaml` (opcional, locks) |
| `plugins/guia/templates/features/lock-ignore.txt` | `features/lock-ignore.txt` (opcional, locks) |

Depois rode `python .guia-fluxo/bin/guia.py init --project-name <nome>` no consumidor para semear `.guia/` e (se copiou os templates de lock) ativar o hook. A automação dessa rota cross-tool (substituta dos installers) está **em aberto** — ver B-004.

## Verificação

```
python .guia-fluxo/bin/guia.py doctor        # rota cópia-manual
```

No Claude (global-first) basta rodar `/guia:status` ou qualquer verbo — o `.guia/` é criado no primeiro comando e o `doctor` passa depois disso. Esperado: `Guia Fluxo files OK.` (Antes de qualquer comando, num projeto ainda não inicializado, o `doctor` lista os arquivos de `.guia/` como ausentes — é esperado; rode um verbo primeiro.)

## Como desinstalar

Estado do processo (`.guia/`, `FEATURES.md`) e dados seus — apague à mão se quiser zerar. No Claude: `/plugin uninstall guia@guia-fluxo`. Na rota cópia-manual: remova `.guia-fluxo/`, `.agents/skills/` e, se ativou locks, `.githooks/commit-msg` + `features/` + `git config --unset core.hooksPath`.

## Quem descobre o que

| Agente | Como descobre o pack | Comandos |
| --- | --- | --- |
| Claude Code | Plugin via marketplace (`/plugin install guia@guia-fluxo`). | `/guia:feature`, `/guia:bug`, `/guia:status`, etc. |
| Codex CLI | Convenção AGENTS.md: lê `.agents/skills/guia-*/SKILL.md`. | skills `guia-feature`, `guia-bug`, etc. |
| Antigravity | Mesma convenção do Codex (AGENTS.md). | idem |

Detalhes da decisão em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md) e [`../adr/0015-plugin-global-first-guia-init.md`](../adr/0015-plugin-global-first-guia-init.md).

## Editando skills (só faz sentido se você é o mantenedor do pack)

Skills são geradas a partir de `core/manifest/manifest.yaml` no repo-mãe. Para alterar:

1. Edite `core/manifest/manifest.yaml` (no repo do pack, não no consumidor).
2. Rode `python core/build/render-skills.py` (regenera `plugins/guia/commands/`, `plugins/guia/.agents/skills/`, `plugins/guia/bin/`, `plugins/guia/templates/`).
3. Em CI, use `python core/build/render-skills.py --check` para barrar drift.

Não edite arquivos sob `plugins/guia/` à mão — são sobrescritos pelo render.
