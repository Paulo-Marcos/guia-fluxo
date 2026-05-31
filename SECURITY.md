# Politica de Seguranca

## Como reportar uma vulnerabilidade

**Nao abra issue publica para falhas de seguranca.** Issue publica expoe todo mundo que usa o pack ate o fix sair.

Reporte em canal privado por uma das vias abaixo:

- **Email:** paulolinhodboa@gmail.com - assunto: `[security] ai-process-pack: <resumo>`
- **GitHub Security Advisory:** botao "Report a vulnerability" na aba *Security* do repositorio (privado por padrao, cria advisory rascunho).

Inclua, se possivel:

- Descricao da falha e impacto observado.
- Passos para reproduzir (comando, input, estado do `.ai/` ou `features/registry.yaml`).
- Versao do pack (`VERSION` ou commit hash).
- Sistema (Windows/Linux/Mac), versao do Python e do Git.
- Sugestao de fix, se tiver.

## O que esperar

- **Acuse de recebimento:** ate **5 dias uteis**.
- **Avaliacao inicial** (severidade, escopo, se reproduz): ate **10 dias uteis** do reporte.
- **Fix:** prazo depende da severidade. Falhas que permitem execucao arbitraria ou bypass do `commit-msg`/lock tem prioridade.
- **Disclosure:** coordenado. So divulgamos a falha publicamente apos haver fix disponivel ou apos prazo razoavel de resposta combinado com o reporter. Credito ao reporter no advisory, salvo pedido em contrario.

Se nao houver resposta em 10 dias uteis, voce esta liberado para escalar (issue publica, divulgacao). Esse e o limite combinado, nao uma ameaca - serve para nao engolir reportes no silencio.

## Escopo

Em escopo (reporte privado):

- Falhas no `scripts/ai.py` / `scripts/ai.ps1` que permitem corromper `.ai/*.json`, `FEATURES.md` ou `features/registry.yaml` de fora do fluxo previsto.
- Bypass do hook `commit-msg` / `bin/check-lock.py` (commitar em arquivo travado sem marca `[unlock:...]`).
- Falhas no `scripts/render-skills.py` que permitem injetar conteudo em `skills/generated/` divergente do manifest.
- Injecao em mensagens de commit, paths, ou inputs de CLI que escapem para shell/Python.
- Vazamento de credenciais ou paths sensiveis em logs/output do CLI.

Fora de escopo (use issue publica normal):

- Bugs funcionais sem impacto de seguranca.
- Sugestoes de melhoria de UX.
- Falhas em projetos terceiros que apenas usam o pack copiado.
- Dependencias de terceiros - reporte upstream (pyyaml, Python, Git).

## Versoes suportadas

Enquanto o pack esta pre-1.0, apenas a versao corrente do branch `main` recebe fix. Veja [`VERSION`](VERSION) e [`CHANGELOG.md`](CHANGELOG.md).

## Camadas defensivas existentes

Contexto para quem investiga: o pack ja tem tres camadas para o lock de arquivos homologados (`docs/explanation/por-que-lock.md`). Falhas que rompem qualquer uma das tres sao tratadas como seguranca:

1. `commit-msg` local (`.githooks/commit-msg` -> `bin/check-lock.py hook`).
2. CI remoto (`.github/workflows/lock-check.yml`, planejado em [F-005](FEATURES.md)).
3. Inspecao manual no PR.
