param(
    [string]$ArduinoCli,
    [string]$NeoPixelLibrary,
    [string]$Fqbn = 'arduino:avr:nano:cpu=atmega328old'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ArduinoCli) {
    $command = Get-Command arduino-cli -ErrorAction SilentlyContinue
    if ($command) { $ArduinoCli = $command.Source }
    else { $ArduinoCli = Join-Path $env:ProgramFiles 'Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe' }
}
if (-not (Test-Path -LiteralPath $ArduinoCli -PathType Leaf)) { throw 'Arduino CLI not found; pass -ArduinoCli.' }
$buildPath = Join-Path $repoRoot 'build-output\native-migration\avr\native'
$arguments = @('compile', '--fqbn', $Fqbn, '--build-path', $buildPath)
if ($NeoPixelLibrary) { $arguments += @('--library', $NeoPixelLibrary) }
$arguments += Join-Path $repoRoot 'firmware\native_car'
# Compile only. Never enumerate ports or upload firmware from this helper.
& $ArduinoCli @arguments
if ($LASTEXITCODE -ne 0) { throw "Arduino compilation failed ($LASTEXITCODE)." }
