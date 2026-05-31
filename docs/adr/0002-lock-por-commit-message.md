# ADR-0002: Unlock por marca no commit-message, nao arquivo separado

- **Status:** Aceita
- **Data:** 2026-05-31

## Contexto

O pack trava arquivos homologados via `features/registry.yaml`. Edicao em arquivo travado precisa de autorizacao explicita, mas onde registrar essa autorizacao?

Opcoes consideradas:

1. Arquivo separado (`features/unlocks.log` ou similar) que lista desbloqueios.
2. Comentario no proprio codigo (`# UNLOCK: <id>`).
3. Marca no commit-message: `[unlock:<id>] motivo: ...`.
4. Branch dedicada para mudancas em arquivos travados.

Cada opcao precisa responder: como auditar 6 meses depois? como evitar que alguem "passe batido"? como nao criar overhead que desencoraja o uso da trava?

## Decisao

Unlock e por commit-message: `[unlock:<feature-id>] motivo: <razao curta>`.

- O hook `commit-msg` rejeita commits que tocam arquivo travado sem a marca.
- O CI re-checa no PR (terceira camada de defesa).
- Cada commit que toca arquivo travado precisa da propria marca - mesmo iterando na mesma feature.

## Consequencias

- + **Auditoria automatica via `git log`** - sem arquivo extra para manter, sem drift entre log e realidade.
- + Marca acompanha a mudanca para sempre: rastreavel mesmo se o branch sumir, mesmo se squash/rebase mover commits.
- + Forca pausa consciente a **cada commit** - se voce esta iterando rapido, cada commit reafirma "estou ciente de que estou mexendo no que esta protegido".
- + Zero overhead de manutencao: nada para sincronizar, nada para revisar, nada para podar.
- + Hook local + CI sao redundantes de proposito - bypass exige dois passos visiveis (`--no-verify` + desligar branch protection).
- - Iteracao em arquivo travado fica verbosa: cada commit repete a marca.
- - Se o desenvolvedor passar `--no-verify` e o repo nao tiver branch protection, a trava nao salva (custo aceito - a trava e pedido consciente, nao prisao).
- - Squash de PR ainda preserva a marca no commit final (ok), mas marcas individuais de commits intermediarios se perdem na historia.

## Alternativas consideradas

- **Arquivo `unlocks.log`:** precisa de processo manual para podar entradas obsoletas. Vira sujeira ou ninguem mantem. Pior para auditoria: arquivo pode ser editado sem deixar rastro no git.
- **Branch dedicada:** acopla "estou mexendo em travado" a estrategia de branching, que ja varia por projeto. Nao funciona em projetos que usam trunk-based.
- **Comentario no codigo:** poluiria o codigo de producao com metadado de processo.

## Links

- Explanation: [`../explanation/por-que-lock.md`](../explanation/por-que-lock.md).
- Convencoes praticas: [`../explanation/convencoes-de-lock.md`](../explanation/convencoes-de-lock.md).
- How-to auditar: [`../how-to/auditar-desbloqueios.md`](../how-to/auditar-desbloqueios.md).
