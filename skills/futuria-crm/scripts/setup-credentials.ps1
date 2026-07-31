[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$stateDir = Join-Path $env:APPDATA "Futuria CRM"
$credentialPath = Join-Path $stateDir "credential.xml"
$configPath = Join-Path $stateDir "config.json"

function Test-LocationId {
    param([string]$Value)
    return $Value -match '^[A-Za-z0-9_-]{6,128}$'
}

if ($Status) {
    $credentialOk = $false
    if (Test-Path -LiteralPath $credentialPath) {
        try {
            $stored = Import-Clixml -LiteralPath $credentialPath
            $credentialOk = $stored -is [System.Management.Automation.PSCredential]
        } catch {
            $credentialOk = $false
        }
    }
    $locationOk = Test-Path -LiteralPath $configPath
    Write-Output ("PIT protetto: {0}" -f $(if ($credentialOk) { "presente" } else { "mancante" }))
    Write-Output ("ID account: {0}" -f $(if ($locationOk) { "presente" } else { "mancante" }))
    exit $(if ($credentialOk -and $locationOk) { 0 } else { 1 })
}

if ($Remove) {
    if (Test-Path -LiteralPath $credentialPath) {
        Remove-Item -LiteralPath $credentialPath -Force
    }
    if (Test-Path -LiteralPath $configPath) {
        Remove-Item -LiteralPath $configPath -Force
    }
    if ((Test-Path -LiteralPath $stateDir) -and -not (Get-ChildItem -LiteralPath $stateDir -Force)) {
        Remove-Item -LiteralPath $stateDir -Force
    }
    Write-Output "Credenziali locali Futuria CRM rimosse. Il PIT remoto non è stato revocato."
    exit 0
}

Write-Host "Configurazione protetta Futuria CRM" -ForegroundColor Cyan
Write-Host "Inserisci i valori in questa finestra. Il PIT non verrà mostrato né scritto nella chat."

$location = (Read-Host "ID del tuo account Futuria CRM").Trim()
if (-not (Test-LocationId $location)) {
    throw "ID account non valido: usa soltanto lettere, numeri, trattino o underscore."
}

$securePit = Read-Host "PIT del tuo account (input nascosto)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePit)
try {
    $plainPit = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    if (-not $plainPit.StartsWith("pit-") -or $plainPit.Length -lt 10) {
        throw "Il PIT non ha il formato atteso. Deve iniziare con pit-."
    }
} finally {
    if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
    $plainPit = $null
}

New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
$credential = [System.Management.Automation.PSCredential]::new("futuria-crm", $securePit)
$credential | Export-Clixml -LiteralPath $credentialPath -Force

@{
    location = $location
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
    storage = "windows-dpapi"
} | ConvertTo-Json | Set-Content -LiteralPath $configPath -Encoding UTF8

Write-Host "Configurazione salvata per l'utente Windows corrente." -ForegroundColor Green
Write-Host "Puoi chiudere questa finestra e tornare all'agente."
