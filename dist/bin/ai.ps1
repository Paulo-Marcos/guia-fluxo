param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CliArgs
)

# `$ErrorActionPreference = "Stop"` faz com que cmdlets PS abortem em erros nao
# tratados em vez de retornar codigo 1 e continuar - alinhado com "fail fast".
$ErrorActionPreference = "Stop"

$MinPythonMajor = 3
$MinPythonMinor = 10


function Test-PythonVersion {
    param([string] $Command)

    if ([string]::IsNullOrWhiteSpace($Command)) {
        return $false
    }

    try {
        $versionScript = "import sys; sys.stdout.write('{0}.{1}'.format(sys.version_info[0], sys.version_info[1]))"
        if ($Command -eq "py") {
            $version = & py -3 -c $versionScript 2>$null
        }
        else {
            $version = & $Command -c $versionScript 2>$null
        }
        if (-not $version) { return $false }
        $parts = $version.Trim().Split('.')
        if ($parts.Count -lt 2) { return $false }
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        return ($major -gt $MinPythonMajor) -or (($major -eq $MinPythonMajor) -and ($minor -ge $MinPythonMinor))
    }
    catch {
        return $false
    }
}


function Get-PythonCandidates {
    $candidates = New-Object System.Collections.Generic.List[string]

    # Camada 1: override explicito.
    if ($env:AI_PROCESS_PYTHON) {
        $candidates.Add($env:AI_PROCESS_PYTHON) | Out-Null
    }

    # Camada 2: venv ativo (achado 3.Q2).
    if ($env:VIRTUAL_ENV) {
        $candidates.Add((Join-Path $env:VIRTUAL_ENV "Scripts\python.exe")) | Out-Null
    }

    # Camada 3: venv local conhecido em ..\..\.venv\.
    $repoPython = Join-Path $PSScriptRoot "..\..\.venv\Scripts\python.exe"
    $candidates.Add($repoPython) | Out-Null

    # Camada 4: launcher py do Windows + executaveis no PATH.
    $candidates.Add("py") | Out-Null
    $candidates.Add("python") | Out-Null
    $candidates.Add("python3") | Out-Null

    # Camada 5: instalacoes per-user descobertas via glob (sem hardcode de versao).
    $userPythons = @()
    if ($env:LOCALAPPDATA) {
        $userBase = Join-Path $env:LOCALAPPDATA "Programs\Python"
        if (Test-Path $userBase) {
            $userPythons += Get-ChildItem $userBase -Directory -Filter "Python3*" -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending |
                ForEach-Object { Join-Path $_.FullName "python.exe" }
        }
    }
    foreach ($userPython in $userPythons) {
        $candidates.Add($userPython) | Out-Null
    }

    # Camada 6: bundle do Codex (opt-in, fallback final).
    if ($env:USERPROFILE) {
        $codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        $candidates.Add($codexPython) | Out-Null
    }

    return ,$candidates
}


function Resolve-Python {
    $candidates = Get-PythonCandidates
    $tried = New-Object System.Collections.Generic.List[string]
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        $tried.Add($candidate) | Out-Null
        if (Test-PythonVersion $candidate) {
            return $candidate
        }
    }
    $report = ($tried | ForEach-Object { "  - $_" }) -join "`n"
    throw @"
Python $MinPythonMajor.$MinPythonMinor+ nao encontrado.
Tentado:
$report

Sugestoes:
  - setar `$env:AI_PROCESS_PYTHON com o path completo
  - ativar um venv (`$env:VIRTUAL_ENV) com Python compativel
  - instalar Python via https://www.python.org/downloads/ ou winget install Python.Python.3
"@
}


$python = Resolve-Python
$script = Join-Path $PSScriptRoot "ai.py"

if (-not (Test-Path $script)) {
    throw "Motor nao encontrado em $script. Confirme que core/src/ai.py existe."
}

if ($python -eq "py") {
    & py -3 $script @CliArgs
}
else {
    & $python $script @CliArgs
}

exit $LASTEXITCODE
