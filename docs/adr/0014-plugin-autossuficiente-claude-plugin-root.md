# ADR-0014: Plugin autossuficiente via `${CLAUDE_PLUGIN_ROOT}`

- **Status:** Aceita
- **Data:** 2026-06-16

## Contexto

As skills renderizadas para o Claude Code (`dist/skills/<verbo>/SKILL.md`) mandavam o agente rodar o motor por caminho **relativo ao diretório de trabalho**: `.\core\bin\guia.ps1 <verbo>` com fallback `python core/src/guia.py <verbo>`. Esses caminhos só existem no repo-fonte do pack.

Num projeto consumidor que instalou o pack via `/plugin install guia@guia-fluxo` (sem clone), não existe pasta `core/` — o comando falhava. A documentação oficial de plugins do Claude Code é explícita: nunca use caminhos relativos ao CWD em comandos; sempre `${CLAUDE_PLUGIN_ROOT}`.

O motor já era empacotado standalone em `dist/bin/guia.py` (o render copia `core/src/*.py` + `core/lock/lock_api.py` para `dist/bin/` flat — F-012). Como o plugin declara `source: ./dist`, quando instalado `${CLAUDE_PLUGIN_ROOT}` aponta para a cópia instalada de `dist/`. Faltava: (1) as skills invocarem por esse caminho, e (2) o motor se ancorar no projeto do consumidor em vez de no local do script, criando o `.guia/` sozinho.

## Decisão

Tornar o plugin autossuficiente — instalável sem clone e sem `init` manual:

1. **Invocação host-aware.** Um partial `_partials/run_cmd.{claude,agent}.md`, incluído via `{{include_per_target: _partials/run_cmd}}` nos bodies de todos os verbos e na Core Rule do `guia-fluxo`. O target `claude_skill` invoca `python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>` (forma bash canônica + nota PowerShell `$env:CLAUDE_PLUGIN_ROOT`). O target `agent_skill` (Codex/Antigravity) mantém o wrapper do repo `core/bin/guia.ps1` com fallback `python core/src/guia.py`.
2. **Raiz do projeto via CWD.** `_constants.ROOT` deixa de ser puramente derivado de `__file__`. Resolução em camadas: override `GUIA_PROJECT_ROOT`; senão a raiz relativa ao script quando ela já contém `.guia/` (mantém o comportamento histórico de repo-fonte, dogfood `dist/bin/` e consumer `install.sh` `.guia-fluxo/bin/`); senão o **CWD exato**. Sem busca para cima por um `.guia/` ancestral — isso sequestraria a raiz para um projeto não-relacionado (mesmo footgun da busca ascendente de `.git`).
3. **Auto-init.** O primeiro comando que toca estado cria o `.guia/` (process.json + estado vazio) se ausente. `init`, `doctor` e `render` ficam de fora (init já semeia; doctor reporta saúde; render é build de manifest).

## Consequências

- + No Claude Code o pack instala sem clone e funciona no primeiro `/guia:feature`, sem `init` manual.
- + Segue a regra oficial de plugins (caminho absoluto via `${CLAUDE_PLUGIN_ROOT}`).
- + Codex/Antigravity não regridem — continuam no deploy próprio para `.guia-fluxo/`.
- + Um único partial host-aware concentra a forma de invocação; mexer nela é um lugar só.
- - Comando agora deve ser rodado a partir da raiz do projeto (sem walk-up para subdiretório). Aceitável: o agente roda do root e há o override `GUIA_PROJECT_ROOT`.
- - **Nuance dogfood:** neste repo as skills ativas vêm de `./dist` (marketplace local), então o agente passa a invocar `dist/bin/guia.py` (motor buildado) em vez de `core/src`. Funciona, e o `render --check` da CI garante o sync. Quem desenvolve o MOTOR continua rodando `core/bin/guia.ps1` direto.

## Alternativas consideradas

- **Comando concreto por verbo com prefixo host-aware embutido:** exigiria um partial por verbo (ou substituição inline), inviável com o include line-level do renderer. Optou-se por um partial genérico com placeholder `<command>` + o comando neutro do verbo logo abaixo.
- **Busca ascendente por `.guia/` a partir do CWD (git-like):** descartada por sequestrar a raiz quando um `.guia/` aparece num ancestral (temp dir, home), quebrando isolamento de testes e podendo apontar para o projeto errado em uso real.

## Links

- [`docs/how-to/instalar-em-outro-projeto.md`](../how-to/instalar-em-outro-projeto.md) — rota sem clone e rota instalador.
- [`docs/adr/0006-plugin-oficial-claude-code.md`](0006-plugin-oficial-claude-code.md) — layout de plugin oficial.
- [`docs/adr/0012-partials-em-bodies.md`](0012-partials-em-bodies.md) e [`0013`](0013-consolidacao-bodies-por-verbo.md) — mecanismo de partials/`include_per_target`.
