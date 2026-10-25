param([switch]$UploadOnly,[string]$CaptureDirectory=(Join-Path $PSScriptRoot '..\captures'))
$ErrorActionPreference='Stop'
$settingsPath=Join-Path $env:APPDATA 'HinaTirt\upload.xml'
if(-not (Test-Path -LiteralPath $settingsPath)){& "$PSScriptRoot\Configure-Upload.ps1"}
$settings=Import-Clixml -LiteralPath $settingsPath
$pythonCommand=Get-Command py.exe -ErrorAction SilentlyContinue
$pythonFlags='-3 '
if(-not $pythonCommand){$pythonCommand=Get-Command python.exe -ErrorAction SilentlyContinue;$pythonFlags=''}
if(-not $pythonCommand){throw 'Python 3.10+ is required. Install Python, then reopen this launcher.'}
$captureRoot=[IO.Path]::GetFullPath($CaptureDirectory)
New-Item -ItemType Directory -Force -Path $captureRoot | Out-Null
$runTag=[guid]::NewGuid().ToString('N')
$stopFile=Join-Path $captureRoot ('.upload-stop-'+$runTag)
$uploadLog=Join-Path $captureRoot ('upload-'+$runTag+'.log')
$uploadErrors=Join-Path $captureRoot ('upload-'+$runTag+'.error.log')
$arguments=$pythonFlags+'"'+(Join-Path $PSScriptRoot 'upload.py')+'" --directory "'+$captureRoot+'" --api "'+$settings.Api+'"'
if(-not $UploadOnly){$arguments+=' --watch --stop-file "'+$stopFile+'"'}
$secretPointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($settings.Token)
$previousToken=$env:TIRT_UPLOAD_TOKEN
try {
 $env:TIRT_UPLOAD_TOKEN=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
 $uploader=Start-Process -FilePath $pythonCommand.Source -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput $uploadLog -RedirectStandardError $uploadErrors
} finally {
 $env:TIRT_UPLOAD_TOKEN=$previousToken
 [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer)
}
try {
 if($UploadOnly){
  $uploader.WaitForExit()
 } else {
  Start-Sleep -Milliseconds 500
  if($uploader.HasExited){throw "Uploader exited. Read $uploadErrors and $uploadLog"}
  Write-Host "Upload worker running. Local data and upload log: $captureRoot"
  Get-PnpDevice -PresentOnly -Class Ports -ErrorAction SilentlyContinue | Select-Object FriendlyName | Format-Table
  $capturePort=Read-Host 'Bluetooth outgoing serial port (COM7 for example)'
  $captureBaud=Read-Host 'Host baud (Enter=9600 for Bluetooth; USB=115200)'
  if(-not $captureBaud){$captureBaud=9600}
  $captureLabel=Read-Host 'Label: LINE BACKGROUND TEXT TRACK MARKER UNLABELLED (Enter=UNLABELLED)'
  if(-not $captureLabel){$captureLabel='UNLABELLED'}
  $captureLabel=$captureLabel.Trim().ToUpperInvariant()
  $labelAliases=@{L='LINE';G='BACKGROUND';T='TEXT';R='TRACK';M='MARKER';U='UNLABELLED'}
  if($labelAliases.ContainsKey($captureLabel)){$captureLabel=$labelAliases[$captureLabel]}
  if($captureLabel -notin @('LINE','BACKGROUND','TEXT','TRACK','MARKER','UNLABELLED')){
   throw 'Unknown label. Use L/G/T/R/M/U or LINE/BACKGROUND/TEXT/TRACK/MARKER/UNLABELLED.'
  }
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\collect.ps1" -Port $capturePort -Baud $captureBaud -Label $captureLabel -Seconds 1800 -OutputDirectory $captureRoot
  $captureResult=$LASTEXITCODE
  Write-Host "Capture exit code: $captureResult"
 }
} finally {
 if(-not $UploadOnly){
  [IO.File]::WriteAllText($stopFile,'stop')
  if(-not $uploader.WaitForExit(15000)){
   Stop-Process -Id $uploader.Id -ErrorAction SilentlyContinue
   Write-Host 'Upload paused. Local pending batches are retained for the next run.'
  }
 }
 if(Test-Path -LiteralPath $uploadLog){Get-Content -LiteralPath $uploadLog -Tail 8}
 if(Test-Path -LiteralPath $uploadErrors){Get-Content -LiteralPath $uploadErrors -Tail 4}
 Write-Host 'Use Retry-Upload.cmd after reconnecting to send pending data. Ending capture does not stop the car.'
 [void](Read-Host 'Press Enter to close')
}
