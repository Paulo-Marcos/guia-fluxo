# Proposta: `bin/release.py` do gerador-cortes compila os fragmentos do CHANGELOG

**Para:** `C:\DEV\gerador-cortes` (`bin/release.py` e
`backend/tests/test_release_d782.py`). **Lá é só leitura** (seção 1 da
especificação): este documento e o patch ao lado são a proposta; aplicar é
decisão do dono, num PR do próprio gerador-cortes.

**Patch:** [`release-py-fragmentos.patch`](release-py-fragmentos.patch),
contra a `origin/main` `0f3e5ca` do gerador-cortes (blobs `d45d670` do
`release.py` e `d2228a0` do teste). Aplica limpo com LF ou CRLF:

```powershell
cd C:\DEV\gerador-cortes   # num worktree da demanda, nunca na PROD
git apply --check C:\DEV\guia-fluxo\docs\propostas\release-py-fragmentos.patch
git apply C:\DEV\guia-fluxo\docs\propostas\release-py-fragmentos.patch
```

## O problema

A R9 tira o conflito do `[Unreleased]`: cada demanda grava o seu
`changelog.d/<ID>.<categoria>.md`, e a release junta tudo. O Guia já faz a
junção (`guia changelog compile`), mas o `release.py` do gerador-cortes lê só
o `CHANGELOG.md`. Com fragmentos no repositório, ele:

- sugeriria o nível **errado** (um `added` em fragmento não conta: um
  `patch` passaria onde a release pede `minor`), ou recusaria por
  `[Unreleased]` vazio;
- lançaria a versão **sem** as entradas dos fragmentos, e eles sobrariam para
  a release seguinte.

## A mudança

No **ato 1** (`preparar`), sem mexer no resto do script:

1. **Ler os fragmentos sem alterar nada.** `ler_fragmentos()` lê
   `changelog.d/*.md`; a função pura `secoes_dos_fragmentos()` agrupa pela
   categoria do nome (`D-886.added.md` → *Added*) e recusa nome fora do padrão
   (categoria inventada decidiria o número errado). `juntar_secoes()` soma o
   `[Unreleased]` escrito à mão e os fragmentos. O `nivel_sugerido()` e o
   `conferir_versao_pedida()` de sempre decidem com tudo — inclusive no
   `--verificar`, que continua sem alterar nada.
2. **Motor explícito, falha cedo.** Com fragmentos, `motor_do_guia()` exige
   `GUIA_PY` (o caminho do `bin/guia.py` do plugin) **antes** do portão de
   minutos; sem ele, a release para com a instrução. O script não adivinha
   onde o plugin está instalado e nunca lança deixando fragmentos de fora.
3. **Compilar depois do portão.** `compilar_fragmentos()` roda
   `guia changelog compile` **sem versão**: os fragmentos entram no
   `[Unreleased]`, e quem fecha a versão (data, links de compare) continua
   sendo o `fechar_unreleased()` do script. Se sobrar fragmento, recusa.
4. **Mesmo commit.** `commitar()` leva as deleções de `changelog.d/` junto do
   CHANGELOG e das cópias da versão; as travas desses arquivos entram com um
   motivo próprio (`MOTIVO_DOS_FRAGMENTOS`), sem reaproveitar o "só o campo
   version sobe".

**Sem `changelog.d/`, nada muda** — o caminho é o de hoje, linha por linha.

## Evidência

- **Testes (7 novos, em `test_release_d782.py`):** agrupamento pela
  categoria, nome fora do padrão recusado, nível decidido só pelos
  fragmentos (`fixed` → patch, `added` → minor, `BREAKING` → minor na 0.y.z),
  soma com o `[Unreleased]` escrito, parada sem `GUIA_PY`, commit levando as
  deleções, motivo próprio da marca. Passam; o único teste que falha na
  cópia isolada (`test_tag_anotada_guarda_os_titulos_das_categorias`, que
  precisa do repositório) falha igual sem o patch.
- **Ponta a ponta com o motor real:** repositório descartável com
  `[Unreleased]` (*Fixed*) e dois fragmentos (`added`, `fixed`), `GUIA_PY`
  apontando para o `core/src/guia.py` do guia-fluxo: nível sugerido `minor`;
  o `compile` juntou os fragmentos (os dois *Fixed* na mesma seção); o
  `gravar_changelog` fechou a 0.7.0 com os links; o commit levou o CHANGELOG
  e as duas deleções, árvore limpa.
- **Estilo do projeto:** `ruff check` e `ruff format --check` do
  `backend/.venv` do gerador-cortes, com o `backend/pyproject.toml` dele,
  limpos no teste (o `bin/` fica fora do portão de lá, como hoje).

## A conferir no primeiro uso

- O `bin/release.ps1` repassa o ambiente: basta
  `$env:GUIA_PY = "<plugin>\bin\guia.py"` antes de chamá-lo.
- O `compile` do Guia lê `delivery.changelog` do `.guia/process.json` do
  gerador-cortes: a adoção dos fragmentos (Onda 7) liga
  `"changelog": {"style": "fragments"}` lá.
- O `check-lock.py check` com caminhos apagados: se alguma trava cobrir
  `changelog.d/`, a marca sai com o motivo dos fragmentos.
