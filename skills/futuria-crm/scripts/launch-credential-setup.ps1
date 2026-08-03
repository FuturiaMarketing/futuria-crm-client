[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$wizardScript = Join-Path $PSScriptRoot "credential-wizard.mjs"
$setupScript = Join-Path $PSScriptRoot "setup-credentials.ps1"

if (Test-Path -LiteralPath $wizardScript) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        $wizardArgument = '"{0}"' -f $wizardScript.Replace('"', '""')
        Start-Process -FilePath $node.Source -ArgumentList $wizardArgument -WindowStyle Hidden | Out-Null
        Write-Output "Configuratore grafico Futuria CRM aperto nel browser."
        exit 0
    }
}

if (-not (Test-Path -LiteralPath $setupScript)) {
    throw "Script di configurazione Futuria CRM non trovato."
}

$argumentLine = '-NoProfile -ExecutionPolicy Bypass -NoExit -File "{0}"' -f $setupScript.Replace('"', '""')
Start-Process -FilePath "powershell.exe" -ArgumentList $argumentLine -WindowStyle Normal | Out-Null
Write-Output "Node.js non è disponibile: aperta la configurazione protetta in PowerShell."
