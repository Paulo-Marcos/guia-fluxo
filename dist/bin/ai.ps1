param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Args
)

$ErrorActionPreference = "Stop"

function Test-Python {
    param([string] $Command)

    if ([string]::IsNullOrWhiteSpace($Command)) {
        return $false
    }

    try {
        if ($Command -eq "py") {
            & py -3 --version *> $null
        }
        else {
            & $Command --version *> $null
        }
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Resolve-Python {
    $localPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
    $repoPython = Join-Path $PSScriptRoot "..\..\.venv\Scripts\python.exe"
    $codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    $candidates = @(
        $env:AI_PROCESS_PYTHON,
        $repoPython,
        "python",
        "python3",
        "py",
        $localPython,
        $codexPython
    )

    foreach ($candidate in $candidates) {
        if (Test-Python $candidate) {
            return $candidate
        }
    }

    throw "Python not found. Set AI_PROCESS_PYTHON or install Python 3.10+."
}

$python = Resolve-Python
$script = Join-Path $PSScriptRoot "ai.py"

if ($python -eq "py") {
    & py -3 $script @Args
}
else {
    & $python $script @Args
}

exit $LASTEXITCODE
