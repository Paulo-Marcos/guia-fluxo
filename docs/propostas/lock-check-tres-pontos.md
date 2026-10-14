# Proposta: `lock-check.yml` do gerador-cortes compara a partir do ponto em que o PR saiu da main

**Para:** `C:\DEV\gerador-cortes\.github\workflows\lock-check.yml` (só leitura daqui; aplicar é decisão do dono,
num PR do próprio gerador-cortes). **Patch:** [`lock-check-tres-pontos.patch`](lock-check-tres-pontos.patch),
contra a `origin/main` `8fa2735` (blob `9fc9009`). Uma linha.

```powershell
cd C:\DEV\gerador-cortes   # num worktree da demanda
git apply --check C:\DEV\guia-fluxo\docs\propostas\lock-check-tres-pontos.patch
git apply C:\DEV\guia-fluxo\docs\propostas\lock-check-tres-pontos.patch
```

## O problema

O passo "Collect changed files" faz `git diff "$BASE" "$HEAD"` (dois pontos), com `BASE` = a ponta atual da `main`
no evento do PR. Quando a `main` anda depois que o PR nasceu, **tudo o que entrou na main aparece como mudança do PR**
— "desfeito" por ele. Se o que entrou na main tocou um arquivo travado, o PR é acusado de mexer numa trava que nunca
tocou. Visto no guia-fluxo nos PRs #53 e #54 (corrigido aqui pela D-168): acusado por `tests/test_configure.py`, mexido pela D-159 na main.

Some sozinho quando a fila atualiza a branch (a base volta a bater), mas confunde quem olha o PR e a auditoria — e,
se o executor ler o check antes de atualizar, devolve o PR à toa (aconteceu no guia-fluxo).

## A mudança

`git diff --name-status ... "$BASE...$HEAD"` (três pontos): o diff parte do *merge-base*, só o que o PR mudou.
No push para a `main` (`BASE` = `before`, ancestral de `HEAD`) o resultado é o mesmo de hoje. O `git log
"$BASE..$HEAD"` das mensagens não muda.

## Validação

No guia-fluxo a mesma correção entrou pela D-168 (PR #57): `tests/test_lock_check_workflow.py` executa o
passo do próprio workflow num repositório sandbox, com a main mudando um teste depois de o PR nascer.
