param([string]$ArduinoCli = "$env:ProgramFiles\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe")
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repoRoot 'firmware\layered_car'
$outputRoot = Join-Path $repoRoot ('build-output\layered-avr-' + [guid]::NewGuid().ToString('N'))
$utf8 = [Text.UTF8Encoding]::new($false)
$results = @()
foreach ($profile in @('practice', 'field-route', 'race-route')) {
    $sketchRoot = Join-Path $outputRoot "$profile\layered_car"
    New-Item -ItemType Directory -Path $sketchRoot -Force | Out-Null
    Copy-Item -LiteralPath "$sourceRoot\motion.h", "$sourceRoot\mission.h", "$sourceRoot\controller.h", "$sourceRoot\layered_car.ino" -Destination $sketchRoot
    if ($profile -ne 'practice') {
        # Compilation fixture only: NOT a verified course or a deployable preset.
        $configName = if ($profile -eq 'race-route') { 'race' } else { 'field' }
        $fixture = @"
static const layered::Step compileFixture[] = {
    {layered::Event::Split, layered::Action::Left, 1000, 20000},
    {layered::Event::Wide, layered::Action::Lift, 1000, 30000},
    {layered::Event::Wide, layered::Action::Finish, 1000, 30000}
};
layered::Controller controller(layered::Config::$configName(), compileFixture, 3);
"@
        $ino = Join-Path $sketchRoot 'layered_car.ino'
        $text = [IO.File]::ReadAllText($ino).Replace('layered::Controller controller(layered::Config::field());', $fixture)
        [IO.File]::WriteAllText($ino, $text, $utf8)
    }
    $buildRoot = Join-Path $outputRoot "$profile\build"
    $log = & $ArduinoCli compile --fqbn arduino:avr:nano:cpu=atmega328old --build-path $buildRoot $sketchRoot 2>&1
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $outputRoot "$profile\compile.log"), ($log -join "`n"), $utf8)
    $log | Write-Output
    if ($exitCode -ne 0) { throw "Layered $profile compilation failed ($exitCode)" }
    $results += [ordered]@{ profile=$profile; fixture_only=($profile -ne 'practice'); uploaded=$false; hex_sha256=(Get-FileHash -LiteralPath "$buildRoot\layered_car.ino.hex").Hash }
}
[IO.File]::WriteAllText((Join-Path $outputRoot 'results.json'), (ConvertTo-Json -InputObject $results -Depth 4), $utf8)
Write-Output "Build receipts: $outputRoot"
