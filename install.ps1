<#
.SYNOPSIS
    Instala o ai-process-pack num projeto consumidor.

.DESCRIPTION
    Copia o build (dist/) deste repo-mae para o layout final do consumidor:

        <Target>/
            .ai-process/             (plugin Claude inteiro, intervalo seguro pra deletar/reinstalar)
                .claude-plugin/      <- dist/.claude-plugin/
                bin/                 <- dist/bin/ (motor standalone, vira PATH automaticamente no Claude)
                skills/              <- dist/skills/ (skills do plugin, namespace ai:)
            .agents/skills/ai-*/     <- dist/.agents/skills/ai-*/ (cross-tool Codex+Antigravity)
            .githooks/commit-msg     <- dist/templates/.githooks/commit-msg (opcional, preserva se existe)
            features/registry.yaml   <- dist/templates/features/registry.yaml (opcional, preserva se existe)
            features/lock-ignore.txt <- dist/templates/features/lock-ignore.txt (opcional, preserva se existe)

    Depois roda `ai init` no consumidor pra semear `.ai/` e `FEATURES.md`.

    Idempotente: re-rodar substitui .ai-process/ e .agents/skills/ pelo build atual,
    preserva templates ja customizados (use -Force pra sobrescrever) e nao toca
    em .ai/ ja inicializada.

.PARAMETER Target
    Diretorio do projeto consumidor. Default: diretorio atual.

.PARAMETER DryRun
    Mostra o que seria feito sem escrever nada no disco.

.PARAMETER Force
    Sobrescreve templates de .githooks/ e features/ mesmo se ja existirem
    no consumidor. Nao afeta .ai-process/ ou .agents/skills/ (esses sempre
    sao substituidos pelo build atual).

.PARAMETER SkipInit
    Nao chamar `ai init` ao final. Util pra debugging ou pra rodar `init`
    com flags customizadas depois.

.EXAMPLE
    .\install.ps1
    Instala no diretorio atual.

.EXAMPLE
    .\install.ps1 -Target C:\dev\meu-projeto
    Instala num projeto especifico.

.EXAMPLE
    .\install.ps1 -DryRun
    Previa: lista as copias sem executar.

.EXAMPLE
    .\install.ps1 -Force
    Sobrescreve .githooks/commit-msg e features/* mesmo se o consumidor ja tem.
#>
[CmdletBinding()]
param(
    [string] $Target = (Get-Location).Path,
    [switch] $DryRun,
    [switch] $Force,
    [switch] $SkipInit
)

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$DistRoot = Join-Path $RepoRoot "dist"

if (-not (Test-Path $DistRoot)) {
    throw "dist/ nao encontrado em $RepoRoot. Rode 'python core/build/render-skills.py' antes."
}

$TargetRoot = (Resolve-Path -LiteralPath $Target).Path

Write-Host ""
Write-Host "ai-process-pack installer" -ForegroundColor Cyan
Write-Host "  origem:  $DistRoot"
Write-Host "  destino: $TargetRoot"
if ($DryRun) { Write-Host "  modo:    DRY-RUN (nada sera escrito)" -ForegroundColor Yellow }
Write-Host ""

function Copy-PluginTree {
    param(
        [Parameter(Mandatory)][string] $Source,
        [Parameter(Mandatory)][string] $Destination,
        [Parameter(Mandatory)][string] $Label
    )

    if (-not (Test-Path $Source)) {
        Write-Host "  skip $Label (origem $Source nao existe)" -ForegroundColor DarkYellow
        return
    }

    Write-Host "  $Label" -ForegroundColor Green
    Write-Host "    $Source"
    Write-Host "      -> $Destination"

    if ($DryRun) { return }

    if (Test-Path $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }
    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
}

function Copy-TemplateFile {
    param(
        [Parameter(Mandatory)][string] $Source,
        [Parameter(Mandatory)][string] $Destination,
        [Parameter(Mandatory)][string] $Label
    )

    if (-not (Test-Path $Source)) {
        Write-Host "  skip $Label (origem $Source nao existe)" -ForegroundColor DarkYellow
        return
    }

    $exists = Test-Path $Destination
    if ($exists -and -not $Force) {
        Write-Host "  keep $Label (ja existe em $Destination; use -Force para sobrescrever)" -ForegroundColor DarkGray
        return
    }

    $verb = if ($exists) { "overwrite" } else { "create" }
    Write-Host "  $verb $Label" -ForegroundColor Green
    Write-Host "    $Source"
    Write-Host "      -> $Destination"

    if ($DryRun) { return }

    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

Write-Host "1) Plugin Claude (.ai-process/)" -ForegroundColor Cyan
$pluginRoot = Join-Path $TargetRoot ".ai-process"
Copy-PluginTree -Source (Join-Path $DistRoot ".claude-plugin") -Destination (Join-Path $pluginRoot ".claude-plugin") -Label ".claude-plugin"
Copy-PluginTree -Source (Join-Path $DistRoot "skills") -Destination (Join-Path $pluginRoot "skills") -Label "skills"
Copy-PluginTree -Source (Join-Path $DistRoot "bin") -Destination (Join-Path $pluginRoot "bin") -Label "bin"

Write-Host ""
Write-Host "2) Cross-tool (.agents/skills/)" -ForegroundColor Cyan
Copy-PluginTree -Source (Join-Path $DistRoot ".agents/skills") -Destination (Join-Path $TargetRoot ".agents/skills") -Label ".agents/skills"

Write-Host ""
Write-Host "3) Templates (preserva customizacao do consumidor)" -ForegroundColor Cyan
Copy-TemplateFile -Source (Join-Path $DistRoot "templates/.githooks/commit-msg") -Destination (Join-Path $TargetRoot ".githooks/commit-msg") -Label ".githooks/commit-msg"
Copy-TemplateFile -Source (Join-Path $DistRoot "templates/features/registry.yaml") -Destination (Join-Path $TargetRoot "features/registry.yaml") -Label "features/registry.yaml"
Copy-TemplateFile -Source (Join-Path $DistRoot "templates/features/lock-ignore.txt") -Destination (Join-Path $TargetRoot "features/lock-ignore.txt") -Label "features/lock-ignore.txt"

if ($SkipInit) {
    Write-Host ""
    Write-Host "4) ai init: SKIPPED (use -SkipInit:`$false ou rode manualmente)" -ForegroundColor DarkGray
}
else {
    Write-Host ""
    Write-Host "4) ai init (semeia .ai/ e FEATURES.md)" -ForegroundColor Cyan
    $enginePath = Join-Path $pluginRoot "bin/ai.py"
    if (-not (Test-Path $enginePath)) {
        Write-Host "  skip (motor nao encontrado em $enginePath; rode manualmente apos investigar)" -ForegroundColor DarkYellow
    }
    elseif ($DryRun) {
        Write-Host "  would run: python `"$enginePath`" init (cwd=$TargetRoot)"
    }
    else {
        Push-Location $TargetRoot
        try {
            & python $enginePath init
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  ai init retornou $LASTEXITCODE - investigue manualmente" -ForegroundColor Yellow
            }
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "Nada foi escrito. Re-rode sem -DryRun para aplicar." -ForegroundColor Yellow
}
else {
    Write-Host "Proximos passos no consumidor:"
    Write-Host "  - Abrir o projeto em Claude Code: o plugin em .ai-process/.claude-plugin/ sera detectado."
    Write-Host "  - Configurar githooks: git config core.hooksPath .githooks"
    Write-Host "  - Rodar 'python .ai-process/bin/ai.py doctor' para verificar."
}
