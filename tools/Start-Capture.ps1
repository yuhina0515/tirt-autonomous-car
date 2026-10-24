$ErrorActionPreference='Stop'
Get-PnpDevice -PresentOnly -Class Ports | Select-Object FriendlyName | Format-Table
$capturePort=Read-Host 'Port (COM7 for example)'
$captureBaud=Read-Host 'Host baud: 115200 for USB, 9600 for tested Bluetooth (Enter=115200)'
if(-not $captureBaud){$captureBaud=115200}
$captureLabel=Read-Host 'Label: LINE BACKGROUND TEXT TRACK MARKER UNLABELLED (Enter=UNLABELLED)'
if(-not $captureLabel){$captureLabel='UNLABELLED'}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\collect.ps1" -Port $capturePort -Baud $captureBaud -Label $captureLabel -Seconds 300
[void](Read-Host 'Press Enter to close')
