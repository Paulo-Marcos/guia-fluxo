param(
    # Verbo de criacao: feature | bug | chore. Posicional 0.
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("feature", "bug", "chore")]
    [string] $Kind,

    # Titulo da demanda. Posicional 1.
    [Parameter(Mandatory = $true, Position = 1)]
    [string] $Title,

    # Prompt inicial opcional para a sessao Claude. Sem isto, a sessao abre
    # nomeada e vazia (o usuario digita o primeiro turno).
    [string] $Prompt,

    # So cria a demanda e imprime o nome canonico; NAO abre o Claude. Util
    # para diagnostico / scripting / quando o `claude` nao esta no PATH.
    [switch] $NoLaunch,

    # Tudo o que sobrar e repassado verbatim ao motor guia (ex.: --context
    # "...", --origin "...", --status planned, --under E-NNN).
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $GuiaArgs
)

# Alinhado com guia.ps1: cmdlets abortam em erro nao tratado (fail fast).
$ErrorActionPreference = "Stop"

# gf.ps1 (D-048) - launcher de terminal que cria a demanda via guia.ps1,
# captura o titulo canonico e abre `claude -n "<titulo>"` para que a nova
# sessao ja nasca nomeada, eliminando o rename pos-criacao.
#
# Viabilidade (verificada em D-048): o Claude Code CLI expoe `-n/--name <name>`
# que define o display name da sessao (prompt box, /resume picker, titulo do
# terminal). Nao foi preciso fallback - o nome na criacao e nativo.
#
# Limitacao consciente: Claude-only. Codex App e Antigravity nao expoem criar
# thread com titulo via API; o slash command in-chat (/guia:feature etc.)
# continua coexistindo como caminho alternativo.

# --- 1. Roda o motor (delega resolucao de Python ao guia.ps1 vizinho) -------
$guiaPs1 = Join-Path $PSScriptRoot "guia.ps1"
if (-not (Test-Path $guiaPs1)) {
    throw "Shim do motor nao encontrado em $guiaPs1. gf.ps1 precisa de guia.ps1 ao lado."
}

# UTF-8 limpo na captura: o titulo canonico tem emoji (✨/🐛/🧹). Sem isto, a
# captura via `&` pode corromper os bytes antes de chegar ao `claude -n`.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$previousOutEnc = [Console]::OutputEncoding
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

try {
    $guiaInvokeArgs = @($Kind, $Title) + $GuiaArgs
    # `&` num .ps1 NAO propaga o `exit` interno (testado em D-048): o codigo
    # volta em $LASTEXITCODE e seguimos. Captura o stdout para parse + echo.
    $captured = & $guiaPs1 @guiaInvokeArgs
    $guiaExit = $LASTEXITCODE
}
finally {
    try { [Console]::OutputEncoding = $previousOutEnc } catch { }
}

# Mostra ao usuario exatamente o que o motor imprimiu (rastreabilidade).
if ($null -ne $captured) {
    $captured | ForEach-Object { Write-Host $_ }
}

if ($guiaExit -ne 0) {
    Write-Error "guia $Kind falhou (exit $guiaExit). Demanda nao criada; Claude nao foi aberto."
    exit $guiaExit
}

# --- 2. Extrai o titulo canonico da demanda ---------------------------------
# O ID e ASCII puro - extrai-se da linha `D-NNN created:` sem risco de
# encoding. E a ancora para casar a fonte correta do titulo.
$demandId = $null
$createdLine = $captured |
    Where-Object { $_ -match '^[A-Z]-\d+ created:' } |
    Select-Object -First 1
if ($createdLine -and ($createdLine -match '^([A-Z]-\d+) created:')) {
    $demandId = $Matches[1]
}

# Titulo via stdout (DEMAND_TITLE= atual; CHAT_TITLE= legado de engine antiga).
# OBS: a captura de stdout pode corromper o emoji do titulo dependendo do
# console - por isso e a fonte SECUNDARIA, nao a primeira.
$stdoutName = $null
$titleLine = $captured |
    Where-Object { $_ -match '^(DEMAND_TITLE|CHAT_TITLE)=' } |
    Select-Object -First 1
if ($titleLine -and ($titleLine -match '^(?:DEMAND_TITLE|CHAT_TITLE)=(.+)$')) {
    $stdoutName = $Matches[1].Trim()
}

# Fonte PRIMARIA: arquivo UTF-8 que set_current_task escreve - emoji intacto.
# So confiamos nele se o ID bater com o `created:` do stdout (defesa contra
# corrida com outra demanda criada em paralelo). demand-title.txt e o atual;
# chat-title.txt o legado.
$fileName = $null
foreach ($leaf in @(".guia/demand-title.txt", ".guia/chat-title.txt")) {
    $candidate = Join-Path (Get-Location) $leaf
    if (Test-Path $candidate) {
        $fromFile = (Get-Content -Raw -Encoding UTF8 $candidate).Trim()
        if ($fromFile) { $fileName = $fromFile; break }
    }
}

$sessionName = $null
if ($fileName -and (-not $demandId -or $fileName -match ("^" + [regex]::Escape($demandId) + "\b"))) {
    # Arquivo casa com a demanda recem-criada: usa-o (UTF-8 fiel).
    $sessionName = $fileName
}
elseif ($stdoutName) {
    # Arquivo ausente ou de outra demanda (corrida): cai no stdout.
    $sessionName = $stdoutName
}
elseif ($fileName) {
    $sessionName = $fileName
}

if (-not $sessionName) {
    Write-Error ("Demanda criada, mas nao consegui capturar o titulo canonico " +
        "(nem DEMAND_TITLE= no stdout nem .guia/demand-title.txt). " +
        "Abra o Claude manualmente e renomeie a sessao.")
    exit 1
}

if (-not $demandId -and $sessionName -match '^([A-Z]-\d+)') {
    $demandId = $Matches[1]
}

# --- 3. Abre o Claude ja nomeado --------------------------------------------
if ($NoLaunch) {
    Write-Host ""
    Write-Host "NOME DA SESSAO: $sessionName"
    Write-Host "(--NoLaunch: Claude nao foi aberto. Rode: claude -n `"$sessionName`")"
    exit 0
}

$claude = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claude) {
    Write-Warning ("`claude` nao encontrado no PATH. Demanda $demandId criada. " +
        "Abra manualmente com:`n  claude -n `"$sessionName`"")
    exit 0
}

$claudeArgs = @("-n", $sessionName)
if ($Prompt) {
    # Prompt posicional do Claude CLI: `claude [options] [prompt]`.
    $claudeArgs += $Prompt
}

Write-Host ""
Write-Host "Abrindo Claude: $sessionName"
& claude @claudeArgs
exit $LASTEXITCODE
