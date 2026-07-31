[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$setupScript = Join-Path $PSScriptRoot "setup-credentials.ps1"
if (-not (Test-Path -LiteralPath $setupScript)) {
    throw "Script di configurazione Futuria CRM non trovato."
}

$argumentLine = '-NoProfile -ExecutionPolicy Bypass -NoExit -File "{0}"' -f $setupScript.Replace('"', '""')
Start-Process -FilePath "powershell.exe" -ArgumentList $argumentLine -WindowStyle Normal | Out-Null
Write-Output "Finestra PowerShell protetta aperta. Attendi che l'utente completi la configurazione."
