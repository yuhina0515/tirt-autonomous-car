param([string]$Api='https://hina-tw.ddns.net/tirt-data')
$ErrorActionPreference='Stop'
$target=[uri]$Api
if($target.Scheme -ne 'https' -or $target.UserInfo -or $target.Query -or $target.Fragment){throw 'An HTTPS API URL is required.'}
$settingsRoot=Join-Path $env:APPDATA 'HinaTirt'
New-Item -ItemType Directory -Force -Path $settingsRoot | Out-Null
$uploadSecret=Read-Host 'Private upload token (hidden)' -AsSecureString
if($uploadSecret.Length -lt 32){throw 'Upload token is too short.'}
[pscustomobject]@{Api=$Api.TrimEnd('/');Token=$uploadSecret} | Export-Clixml -LiteralPath (Join-Path $settingsRoot 'upload.xml')
Write-Host 'Saved encrypted upload credentials for this Windows user on this computer.'
