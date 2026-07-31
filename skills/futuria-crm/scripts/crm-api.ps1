[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("GET", "POST", "PUT", "PATCH", "DELETE")]
    [string]$Method,

    [Parameter(Mandatory = $true)]
    [string]$Path,

    [string]$Body,
    [string]$BodyFile,
    [string]$Version = "2021-07-28"
)

$ErrorActionPreference = "Stop"
$stateDir = Join-Path $env:APPDATA "Futuria CRM"
$credentialPath = Join-Path $stateDir "credential.xml"
$configPath = Join-Path $stateDir "config.json"

$location = @($env:FUTURIA_CRM_LOCATION, $env:FUTURIA_CRM_LOCATION_ID) |
    Where-Object { $_ } | Select-Object -First 1
if (-not $location -and (Test-Path -LiteralPath $configPath)) {
    $location = (Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json).location
}

$token = $env:FUTURIA_CRM_TOKEN
if (-not $token -and (Test-Path -LiteralPath $credentialPath)) {
    $stored = Import-Clixml -LiteralPath $credentialPath
    if ($stored -isnot [System.Management.Automation.PSCredential]) {
        throw "Archivio credenziali Futuria CRM non valido."
    }
    $token = $stored.GetNetworkCredential().Password
}

if (-not $token -or -not $location) {
    throw "Credenziali Futuria CRM mancanti. Esegui prima setup-credentials.ps1 in una finestra separata."
}
if (-not $token.StartsWith("pit-")) {
    throw "Il PIT configurato non ha il formato atteso."
}
if ([string]$location -notmatch '^[A-Za-z0-9_-]{6,128}$') {
    throw "L'ID account configurato non ha il formato atteso."
}
if ($Version -notmatch '^(v[0-9]+|[0-9]{4}-[0-9]{2}-[0-9]{2})$') {
    throw "La versione API richiesta non ha il formato atteso."
}
if (-not $Path.StartsWith("/") -or $Path.Contains("://")) {
    throw "Il percorso API deve essere relativo e iniziare con /. URL esterni non sono consentiti."
}

$safeLocation = [Uri]::EscapeDataString([string]$location)
$resolvedPath = $Path.Replace("{location}", $safeLocation)
$uri = "https://services.leadconnectorhq.com" + $resolvedPath
$headers = @{
    Authorization = "Bearer $token"
    Version = $Version
    Accept = "application/json"
}

if ($Body -and $BodyFile) {
    throw "Usa Body oppure BodyFile, non entrambi."
}
if ($BodyFile) {
    $Body = Get-Content -Raw -Encoding UTF8 -LiteralPath $BodyFile
}
if ($Body) {
    $Body = $Body.Replace("{location}", [string]$location)
}

try {
    $params = @{
        Method = $Method
        Uri = $uri
        Headers = $headers
    }
    if ($Body) {
        $params.ContentType = "application/json"
        $params.Body = [Text.Encoding]::UTF8.GetBytes($Body)
    }
    $response = Invoke-RestMethod @params
    if ($null -ne $response) {
        $response | ConvertTo-Json -Depth 100
    }
} catch {
    $status = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $status = [int]$_.Exception.Response.StatusCode
    }
    $detail = $_.ErrorDetails.Message
    if (-not $detail) {
        $detail = $_.Exception.Message
    }
    throw "Errore Futuria CRM$(if ($status) { " HTTP $status" }): $detail"
} finally {
    $token = $null
    $headers.Authorization = $null
}
