param(
    [string] $Path
)

# guia-rename.ps1 - helper fino de renomeacao de chat (D-057).
#
# NAO renomeia a sessao Claude Code: nao existe mecanismo externo para
# retitular uma sessao JA ABERTA (verificado em D-057; `claude -n` so vale
# no lancamento = D-048; `/rename` e slash command humano dentro do chat).
# O que este script faz: le `.guia/demand-title.txt` (titulo da demanda
# corrente, escrito pelo motor), COPIA para a area de transferencia e
# imprime destacado - para voce so dar `/rename` + colar (Ctrl+V).
#
# Pos-D-093: chat != demanda; renomear e conveniencia OPCIONAL. Pule quando
# o chat agrega varias demandas (ex.: um epico e suas stories).

$ErrorActionPreference = "Stop"


function Find-DemandTitleFile {
    param([string] $Override)

    if ($Override) {
        if (-not (Test-Path $Override)) {
            throw "Arquivo nao encontrado: $Override"
        }
        return (Resolve-Path $Override).Path
    }

    # Sobe a partir do cwd procurando .guia/demand-title.txt.
    $dir = (Get-Location).Path
    while ($dir) {
        $candidate = Join-Path $dir ".guia\demand-title.txt"
        if (Test-Path $candidate) {
            return $candidate
        }
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    throw "Nao achei .guia/demand-title.txt subindo a partir de $((Get-Location).Path). Rode dentro de um projeto Guia Fluxo, ou passe -Path."
}


$file = Find-DemandTitleFile -Override $Path

# Primeira linha nao-vazia, sem espacos nas pontas.
$title = (Get-Content -LiteralPath $file -Encoding UTF8 |
    Where-Object { $_.Trim() -ne "" } |
    Select-Object -First 1)

if (-not $title) {
    Write-Host "demand-title.txt esta vazio ($file)." -ForegroundColor Yellow
    Write-Host "Rode um comando do guia (start/ready/finish...) para popular o titulo da demanda corrente."
    exit 1
}

$title = $title.Trim()

try {
    Set-Clipboard -Value $title
    $copied = $true
}
catch {
    $copied = $false
}

Write-Host ""
Write-Host "  NOME DA DEMANDA:" -ForegroundColor Cyan
Write-Host "  $title" -ForegroundColor White
Write-Host ""
if ($copied) {
    Write-Host "  Copiado para a area de transferencia." -ForegroundColor Green
    Write-Host "  No chat: digite /rename e cole (Ctrl+V)."
}
else {
    Write-Host "  (Nao consegui copiar para o clipboard - copie a linha acima a mao.)" -ForegroundColor Yellow
    Write-Host "  No chat: /rename <cole o titulo>"
}
Write-Host ""
